import frappe
from frappe import _
import random
import jwt
import datetime

# Secret key for JWT encoding/decoding (minimum 32 bytes)
DEFAULT_JWT_SECRET = "clinic_satusehat_patient_auth_secret_key_2026_v1"

def get_jwt_secret():
	return frappe.conf.get("jwt_secret") or DEFAULT_JWT_SECRET

def verify_token_payload(token=None):
	"""
	Helper to verify patient token and return decoded payload.
	Checks token parameter, X-Patient-Token header, or Authorization header.
	"""
	if not token:
		token = frappe.get_request_header("X-Patient-Token") or frappe.form_dict.get("token")

	if not token:
		auth_header = frappe.get_request_header("Authorization")
		if auth_header and auth_header.startswith("Bearer "):
			token = auth_header.split(" ")[1]

	if not token:
		frappe.throw(_("Token autentikasi pasien tidak ditemukan"), frappe.PermissionError)

	try:
		payload = jwt.decode(token, get_jwt_secret(), algorithms=["HS256"])
		return payload
	except jwt.ExpiredSignatureError:
		frappe.throw(_("Sesi login telah kedaluwarsa, silakan login kembali"), frappe.PermissionError)
	except jwt.InvalidTokenError:
		frappe.throw(_("Token autentikasi tidak valid"), frappe.PermissionError)

@frappe.whitelist(allow_guest=True)
def send_patient_otp(email=None, identifier=None):
	"""
	Generate and send 6-digit OTP to patient's registered email/phone.
	Accepts either 'email' or 'identifier' (matches email, mobile, or NIK).
	"""
	search_key = (identifier or email or "").strip()
	if not search_key:
		frappe.throw(_("Email atau Nomor HP wajib diisi"), frappe.MandatoryError)

	# Search Patient by email or mobile
	patient_list = frappe.db.sql("""
		SELECT name, patient_name, email, mobile, uid
		FROM `tabPatient`
		WHERE (email IS NOT NULL AND LOWER(email) = %s)
		   OR (mobile IS NOT NULL AND mobile = %s)
		ORDER BY creation DESC
		LIMIT 1
	""", (search_key.lower(), search_key), as_dict=True)

	if not patient_list:
		frappe.throw(_("Pasien dengan '{0}' tidak ditemukan di sistem").format(search_key), frappe.DoesNotExistError)

	patient = patient_list[0]
	target_email = patient.email or search_key

	# Generate 6-digit OTP
	otp_code = str(random.randint(100000, 999999))

	# Save OTP to Redis cache (5 minutes expiration = 300s)
	cache_key = f"patient_otp:{search_key.lower()}"
	frappe.cache().set_value(cache_key, otp_code, expires_in_sec=300)
	if patient.email:
		frappe.cache().set_value(f"patient_otp:{patient.email.lower()}", otp_code, expires_in_sec=300)
	if patient.mobile:
		frappe.cache().set_value(f"patient_otp:{patient.mobile}", otp_code, expires_in_sec=300)

	# Send OTP email if email exists
	has_outgoing_account = frappe.db.exists("Email Account", {"default_outgoing": 1, "enable_outgoing": 1})
	if patient.email and has_outgoing_account:
		subject = f"[{frappe.db.get_default('system_name') or 'DAU SIMRS'}] Kode OTP Login Anda: {otp_code}"
		message = f"""
			<div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 500px; margin: 0 auto; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
				<div style="background-color: #2b6cb0; color: #ffffff; padding: 20px; text-align: center;">
					<h2 style="margin: 0; font-size: 20px;">Layanan Pasien Online</h2>
				</div>
				<div style="padding: 24px; background-color: #ffffff; color: #2d3748;">
					<p style="margin-top: 0;">Halo <b>{patient.patient_name}</b>,</p>
					<p>Berikut adalah kode OTP untuk verifikasi login akun Anda:</p>
					<div style="text-align: center; margin: 24px 0;">
						<span style="font-size: 32px; font-weight: bold; color: #2b6cb0; letter-spacing: 6px; background-color: #ebf8ff; padding: 12px 24px; border-radius: 6px; border: 1px dashed #3182ce; display: inline-block;">
							{otp_code}
						</span>
					</div>
					<p style="font-size: 14px; color: #718096;">
						⏱️ Kode OTP ini berlaku selama <b>5 menit</b>. Jangan berikan kode ini kepada orang lain.
					</p>
				</div>
			</div>
		"""
		try:
			frappe.sendmail(
				recipients=[patient.email],
				subject=subject,
				message=message,
				now=True
			)
		except Exception as e:
			frappe.log_error(f"Gagal mengirim email OTP ke {patient.email}: {str(e)}", "Patient OTP Mail Error")
	else:
		frappe.log_error(
			f"Email server belum dikonfigurasi / email kosong. Kode OTP untuk {search_key} adalah: {otp_code}",
			"Patient OTP Dev Mode"
		)

	# Clear internal msgprint logs to prevent red _server_messages in API response
	if hasattr(frappe.local, "message_log"):
		frappe.local.message_log = []

	response = {
		"status": "success",
		"message": f"Kode OTP berhasil dikirimkan",
		"identifier": search_key
	}

	if not has_outgoing_account or not patient.email:
		response["dev_note"] = "Email Account SMTP belum disetup di Desk Frappe. Gunakan otp_debug untuk pengujian."
		response["otp_debug"] = otp_code

	return response

@frappe.whitelist(allow_guest=True)
def verify_patient_otp(email=None, identifier=None, otp_code=None):
	"""
	Verify 6-digit OTP and return JWT login token + patient info.
	"""
	search_key = (identifier or email or "").strip()
	if not search_key or not otp_code:
		frappe.throw(_("Email/Nomor HP dan Kode OTP wajib diisi"), frappe.MandatoryError)

	otp_code = str(otp_code).strip()
	cache_key = f"patient_otp:{search_key.lower()}"
	saved_otp = frappe.cache().get_value(cache_key)

	if not saved_otp:
		frappe.throw(_("Kode OTP telah kedaluwarsa atau belum diminta. Silakan minta OTP baru."), frappe.AuthenticationError)

	if str(saved_otp) != otp_code:
		frappe.throw(_("Kode OTP yang Anda masukkan salah"), frappe.AuthenticationError)

	# Delete from Redis cache to prevent reuse
	frappe.cache().delete_value(cache_key)

	# Retrieve Patient details
	patient_list = frappe.db.sql("""
		SELECT name, patient_name, email, uid, mobile, dob, sex, blood_group
		FROM `tabPatient`
		WHERE (email IS NOT NULL AND LOWER(email) = %s)
		   OR (mobile IS NOT NULL AND mobile = %s)
		ORDER BY creation DESC
		LIMIT 1
	""", (search_key.lower(), search_key), as_dict=True)

	if not patient_list:
		frappe.throw(_("Data pasien tidak ditemukan"), frappe.DoesNotExistError)

	patient = patient_list[0]

	# Generate JWT Token (7 days validity)
	expiration = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)
	payload = {
		"patient_id": patient.name,
		"patient_name": patient.patient_name,
		"email": patient.email,
		"exp": expiration
	}

	token = jwt.encode(payload, get_jwt_secret(), algorithm="HS256")

	return {
		"status": "success",
		"message": "Verifikasi OTP berhasil",
		"token": token,
		"patient": patient
	}

@frappe.whitelist(allow_guest=True)
def register_patient(name, nik, gender, dob, phone, email):
	"""
	Register a new patient, create Patient doc in Frappe, and return JWT token.
	"""
	if not name or not nik or not email or not phone:
		frappe.throw(_("Nama, NIK, Phone, dan Email wajib diisi"), frappe.MandatoryError)

	name = name.strip()
	nik = str(nik).strip()
	email = email.strip().lower()
	phone = str(phone).strip()

	# Check if NIK already exists
	existing_by_nik = frappe.db.get_value("Patient", {"uid": nik}, "name")
	if existing_by_nik:
		frappe.throw(_("NIK '{0}' sudah terdaftar pada sistem (ID Pasien: {1}). Silakan login.").format(nik, existing_by_nik), frappe.DuplicateEntryError)

	# Check if Email already exists
	existing_by_email = frappe.db.get_value("Patient", {"email": email}, "name")
	if existing_by_email:
		frappe.throw(_("Email '{0}' sudah terdaftar pada sistem. Silakan login.").format(email), frappe.DuplicateEntryError)

	sex = "Male" if gender in ["Laki-laki", "Male"] else "Female"

	patient = frappe.get_doc({
		"doctype": "Patient",
		"first_name": name,
		"patient_name": name,
		"uid": nik,
		"sex": sex,
		"dob": dob,
		"mobile": phone,
		"email": email
	})
	patient.insert(ignore_permissions=True)

	# Generate JWT Token (7 days validity)
	expiration = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)
	payload = {
		"patient_id": patient.name,
		"patient_name": patient.patient_name,
		"email": patient.email,
		"exp": expiration
	}
	token = jwt.encode(payload, get_jwt_secret(), algorithm="HS256")

	return {
		"status": "success",
		"message": "Pendaftaran rekam medis pasien berhasil",
		"token": token,
		"patient": {
			"name": patient.name,
			"patient_name": patient.patient_name,
			"email": patient.email,
			"uid": patient.uid,
			"mobile": patient.mobile,
			"dob": str(patient.dob) if patient.dob else None,
			"sex": patient.sex,
			"blood_group": getattr(patient, "blood_group", None)
		}
	}

@frappe.whitelist(allow_guest=True)
def get_patient_profile(token=None):
	"""
	Get profile information of currently authenticated patient using JWT Token.
	"""
	payload = verify_token_payload(token)
	patient_id = payload.get("patient_id")

	patient = frappe.get_doc("Patient", patient_id)
	
	# Fetch active appointments from Patient Appointment
	active_registrations = frappe.db.get_all(
		"Patient Appointment",
		filters={"patient": patient_id, "status": ["not in", ["Closed", "Cancelled", "Completed"]]},
		fields=["name", "appointment_date", "appointment_time", "department", "practitioner", "status"],
		order_by="creation desc",
		limit=5
	)

	return {
		"status": "success",
		"patient": {
			"name": patient.name,
			"patient_name": patient.patient_name,
			"email": patient.email,
			"uid": getattr(patient, "uid", None),
			"mobile": patient.mobile,
			"dob": str(patient.dob) if patient.dob else None,
			"sex": patient.sex,
			"blood_group": patient.blood_group
		},
		"active_registrations": active_registrations
	}

@frappe.whitelist(allow_guest=True)
def get_patient_appointments(token=None):
	"""
	API: Mengambil daftar riwayat janji temu pasien saat ini dari Doctype Patient Appointment berdasarkan token session
	"""
	payload = verify_token_payload(token)
	patient_id = payload.get("patient_id")

	appointments = frappe.db.get_all(
		"Patient Appointment",
		filters={"patient": patient_id},
		fields=[
			"name", "patient_name", "practitioner", "practitioner_name",
			"department", "company", "appointment_date", "appointment_time",
			"mode_of_payment", "status", "creation", "notes"
		],
		order_by="creation desc"
	)

	from clinic_satusehat.api.hospital_search import format_doctor_data

	formatted_list = []
	for app in appointments:
		practitioner_doc = None
		if app.practitioner and frappe.db.exists("Healthcare Practitioner", app.practitioner):
			practitioner_doc = frappe.get_doc("Healthcare Practitioner", app.practitioner)

		doctor_data = format_doctor_data(practitioner_doc) if practitioner_doc else {
			"id": app.practitioner or "dr-default",
			"name": app.practitioner_name or app.practitioner or "Dokter Spesialis",
			"poly": app.department or "Penyakit Dalam",
			"hospital": app.company or "RS Andalan",
			"avatarUrl": "https://images.unsplash.com/photo-1622253692010-333f2da6031d?w=400&auto=format&fit=crop&q=80",
		}

		raw_status = (app.status or "Open").strip()
		status_lower = raw_status.lower()

		if status_lower in ["closed", "completed", "selesai"]:
			fe_status = "COMPLETED"
		elif status_lower in ["cancelled", "dibatalkan"]:
			fe_status = "CANCELLED"
		else:
			fe_status = "UPCOMING"

		try:
			doc_num = int(app.name.split("-")[-1])
			queue_num = f"A-{doc_num:03d}"
		except Exception:
			queue_num = "A-001"

		formatted_list.append({
			"id": app.name,
			"bookingCode": app.name,
			"queueNumber": queue_num,
			"doctor": doctor_data,
			"patientName": app.patient_name or "Pasien",
			"appointmentDate": str(app.appointment_date),
			"appointmentTime": str(app.appointment_time)[:5] if app.appointment_time else "09:00",
			"polyClinic": app.department or doctor_data.get("poly", "Penyakit Dalam"),
			"paymentMethod": app.mode_of_payment or "Tunai / Cash",
			"status": fe_status,
			"frappeStatus": raw_status,
			"qrCodeValue": app.name,
			"creation": str(app.creation)
		})

	return {
		"status": "success",
		"appointments": formatted_list
	}

@frappe.whitelist(allow_guest=True)
def create_patient_appointment(
	token=None,
	practitioner=None,
	appointment_date=None,
	appointment_time=None,
	mode_of_payment=None,
	insurance_name=None,
	company_name=None,
	bpjs_number=None,
	patient_notes=None
):
	"""
	API: Membuat Pendaftaran Janji Temu Pasien di Frappe
	"""
	if not practitioner or not appointment_date or not appointment_time:
		frappe.throw(_("Dokter, Tanggal, dan Jam Berobat wajib diisi"), frappe.MandatoryError)

	payload = verify_token_payload(token)
	patient_id = payload.get("patient_id")

	# Parse & format appointment_date to standard YYYY-MM-DD format
	if appointment_date:
		try:
			parsed = frappe.utils.getdate(appointment_date)
			appointment_date = str(parsed)
		except Exception:
			frappe.throw(_("Format tanggal berobat '{0}' tidak valid").format(appointment_date), frappe.ValidationError)

	patient = frappe.get_doc("Patient", patient_id)
	practitioner_doc = frappe.get_doc("Healthcare Practitioner", practitioner)

	# Check if slot is already booked for this practitioner and date
	from clinic_satusehat.api.hospital_search import format_time_str
	time_clean = format_time_str(appointment_time)

	existing_booking = frappe.db.sql("""
		SELECT name
		FROM `tabPatient Appointment`
		WHERE practitioner = %s
		  AND appointment_date = %s
		  AND TIME_FORMAT(appointment_time, '%%H:%%i') = %s
		  AND status NOT IN ('Cancelled', 'Dibatalkan')
		LIMIT 1
	""", (practitioner_doc.name, appointment_date, time_clean))

	if existing_booking:
		frappe.throw(
			_("Jam berobat {0} pada tanggal {1} sudah dipesan oleh pasien lain. Silakan pilih jam/sesi berobat yang lain.").format(time_clean, appointment_date),
			frappe.DuplicateEntryError
		)

	# Company fallback
	company = getattr(practitioner_doc, "hospital", None)
	if not company or not frappe.db.exists("Company", company):
		company = frappe.db.get_single_value("Global Defaults", "default_company") or "RS Andalan"

	# Generate Booking Code & Queue Number based on doc name
	app_type = frappe.db.get_value("Appointment Type", {"name": "Doctor Appointment"}, "name") or frappe.db.get_value("Appointment Type", {}, "name")

	# Resolve Mode of Payment link
	mop = mode_of_payment
	if mop and not frappe.db.exists("Mode of Payment", mop):
		mop_lower = mop.lower()
		if "bpjs" in mop_lower:
			mop = "BPJS"
		elif "asuran" in mop_lower or "insur" in mop_lower:
			mop = "Asurance"
		elif "perusahaan" in mop_lower or "company" in mop_lower or "guarantee" in mop_lower:
			mop = "Company Guarantee"
		elif "cash" in mop_lower or "tunai" in mop_lower:
			mop = "Cash"
		else:
			mop = frappe.db.get_value("Mode of Payment", {}, "name") or "Cash"

	appointment_doc = frappe.get_doc({
		"doctype": "Patient Appointment",
		"patient": patient.name,
		"patient_name": patient.patient_name,
		"practitioner": practitioner_doc.name,
		"department": practitioner_doc.department,
		"company": company,
		"appointment_date": appointment_date,
		"appointment_time": appointment_time,
		"appointment_type": app_type,
		"appointment_for": "Practitioner",
		"mode_of_payment": mop,
		"notes": f"Catatan: {patient_notes or '-'}\nMetode Input: {mode_of_payment}\nBPJS: {bpjs_number or '-'}\nAsuransi/Company: {insurance_name or company_name or '-'}",
		"status": "Open"
	})
	appointment_doc.insert(ignore_permissions=True)

	booking_code = appointment_doc.name
	try:
		doc_num = int(appointment_doc.name.split("-")[-1])
		queue_num = f"A-{doc_num:03d}"
	except Exception:
		queue_num = "A-001"

	return {
		"status": "success",
		"message": "Pendaftaran janji temu berhasil dibuat",
		"booking_code": booking_code,
		"queue_number": queue_num,
		"appointment_id": appointment_doc.name,
		"appointment": {
			"id": appointment_doc.name,
			"booking_code": booking_code,
			"queue_number": queue_num,
			"patient": patient.patient_name,
			"practitioner": practitioner_doc.practitioner_name,
			"department": practitioner_doc.department,
			"appointment_date": str(appointment_date),
			"appointment_time": str(appointment_time),
			"mode_of_payment": mode_of_payment
		}
	}

@frappe.whitelist(allow_guest=True)
def get_appointment_detail(appointment_id):
	"""
	API: Mengambil detail Patient Appointment berdasarkan ID (name / HLC-APP-XXXX)
	"""
	if not appointment_id:
		frappe.throw(_("ID Janji Temu (Appointment ID) wajib diisi"), frappe.MandatoryError)

	appointment_doc = None
	if frappe.db.exists("Patient Appointment", appointment_id):
		appointment_doc = frappe.get_doc("Patient Appointment", appointment_id)
	else:
		apps = frappe.db.get_all("Patient Appointment", filters={"name": ["like", f"%{appointment_id}%"]}, limit=1)
		if apps:
			appointment_doc = frappe.get_doc("Patient Appointment", apps[0].name)

	if not appointment_doc:
		frappe.throw(_("Data Janji Temu '{0}' tidak ditemukan").format(appointment_id), frappe.DoesNotExistError)

	patient_name = appointment_doc.patient_name or frappe.db.get_value("Patient", appointment_doc.patient, "patient_name") or "Pasien"

	practitioner_doc = None
	if appointment_doc.practitioner and frappe.db.exists("Healthcare Practitioner", appointment_doc.practitioner):
		practitioner_doc = frappe.get_doc("Healthcare Practitioner", appointment_doc.practitioner)

	from clinic_satusehat.api.hospital_search import format_doctor_data
	doctor_data = format_doctor_data(practitioner_doc) if practitioner_doc else {
		"id": appointment_doc.practitioner or "dr-default",
		"name": getattr(appointment_doc, "practitioner_name", None) or appointment_doc.practitioner or "Dokter Spesialis",
		"poly": appointment_doc.department or "Penyakit Dalam",
		"hospital": appointment_doc.company or "RS Andalan",
		"avatarUrl": "https://images.unsplash.com/photo-1622253692010-333f2da6031d?w=400&auto=format&fit=crop&q=80",
	}

	try:
		doc_num = int(appointment_doc.name.split("-")[-1])
		queue_num = f"A-{doc_num:03d}"
	except Exception:
		queue_num = "A-001"

	return {
		"status": "success",
		"appointment": {
			"id": appointment_doc.name,
			"booking_code": getattr(appointment_doc, "booking_code", None) or appointment_doc.name,
			"queue_number": queue_num,
			"patient_name": patient_name,
			"doctor": doctor_data,
			"department": appointment_doc.department,
			"company": appointment_doc.company,
			"appointment_date": str(appointment_doc.appointment_date),
			"appointment_time": str(appointment_doc.appointment_time)[:5] if appointment_doc.appointment_time else "09:00",
			"mode_of_payment": appointment_doc.mode_of_payment or "Tunai / Cash",
			"status": appointment_doc.status or "Open",
			"notes": appointment_doc.notes
		}
	}
