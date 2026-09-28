import frappe
from frappe import _
import random
import jwt
import datetime
import json

import base64
from frappe.utils.file_manager import save_file

# Secret key for JWT encoding/decoding (minimum 32 bytes)
DEFAULT_JWT_SECRET = "clinic_satusehat_patient_auth_secret_key_2026_v1"

def get_jwt_secret():
	return frappe.conf.get("jwt_secret") or DEFAULT_JWT_SECRET

def save_patient_uploaded_file(patient_id, fieldname, file_data_url):
	"""
	Decodes Base64 data URL from frontend file uploader and saves as a real File document in Frappe public/files/.
	Returns the file URL string (/files/...).
	"""
	if not file_data_url or not isinstance(file_data_url, str):
		return ""

	if file_data_url.startswith("data:"):
		try:
			header, base64_str = file_data_url.split(",", 1)
			mime = header.split(";")[0].split(":")[1] if ";" in header else "image/png"
			ext = "png"
			if "pdf" in mime:
				ext = "pdf"
			elif "jpeg" in mime or "jpg" in mime:
				ext = "jpg"
			elif "png" in mime:
				ext = "png"
			elif "/" in mime:
				ext = mime.split("/")[1]

			file_bytes = base64.b64decode(base64_str)
			clean_id = patient_id.replace("/", "_").replace(" ", "_")
			filename = f"{fieldname}_{clean_id}.{ext}"

			file_doc = save_file(
				fname=filename,
				content=file_bytes,
				dt="Patient",
				dn=patient_id,
				is_private=0
			)
			return file_doc.file_url
		except Exception as e:
			frappe.log_error(title="Patient Upload File Error", message=f"Gagal menyimpan berkas {fieldname} pasien {patient_id}: {str(e)}")
			return ""
	return file_data_url

def parse_patient_guarantee(patient):
	v_status = getattr(patient, "custom_verification_status", None) or "Approved"
	v_notes = getattr(patient, "custom_verification_notes", None) or ""

	guarantee = {
		"mode_of_payment": getattr(patient, "custom_mode_of_payment", None) or "Cash",
		"bpjs_number": getattr(patient, "custom_bpjs_number", None) or "",
		"bpjs_referral_file": getattr(patient, "custom_bpjs_referral_file", None) or "",
		"company_name": getattr(patient, "custom_company_name", None) or "",
		"company_guarantee_file": getattr(patient, "custom_company_guarantee_file", None) or "",
		"insurance_name": getattr(patient, "custom_insurance_name", None) or "",
		"insurance_card_file": getattr(patient, "custom_insurance_card_file", None) or "",
		"verification_status": v_status,
		"verification_notes": v_notes
	}
	details_str = getattr(patient, "patient_details", None)
	if details_str:
		try:
			data = json.loads(details_str)
			if isinstance(data, dict):
				for k, v in data.items():
					if not guarantee.get(k):
						guarantee[k] = v
		except Exception:
			pass
	return guarantee

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
	Checks if patient verification is Approved before sending OTP.
	"""
	search_key = (identifier or email or "").strip()
	if not search_key:
		frappe.throw(_("Email atau Nomor HP wajib diisi"), frappe.MandatoryError)

	# Search Patient by email or mobile
	patient_list = frappe.db.sql("""
		SELECT name, patient_name, email, mobile, uid, custom_verification_status, custom_verification_notes
		FROM `tabPatient`
		WHERE (email IS NOT NULL AND LOWER(email) = %s)
		   OR (mobile IS NOT NULL AND mobile = %s)
		ORDER BY creation DESC
		LIMIT 1
	""", (search_key.lower(), search_key), as_dict=True)

	if not patient_list:
		frappe.throw(_("Pasien dengan '{0}' tidak ditemukan di sistem").format(search_key), frappe.DoesNotExistError)

	patient = patient_list[0]

	# Verification status check
	v_status = (patient.get("custom_verification_status") or "Approved").strip()
	if v_status in ["Pending Verification", "Pending", "Belum Diverifikasi"]:
		frappe.throw(
			_("Akun pasien '{0}' sedang dalam proses verifikasi berkas. Silakan tunggu konfirmasi sebelum login.").format(patient.patient_name),
			frappe.PermissionError
		)
	if v_status in ["Rejected", "Ditolak"]:
		notes = patient.get("custom_verification_notes") or "Silakan hubungi customer service RS."
		frappe.throw(
			_("Pendaftaran akun pasien '{0}' ditolak oleh Admin SIMRS. Catatan: {1}").format(patient.patient_name, notes),
			frappe.PermissionError
		)

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
	mail_sent = False
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
				now=False
			)
			from frappe.email.queue import flush
			flush()
			mail_sent = True
		except Exception as e:
			frappe.log_error(title="Patient OTP Mail Error", message=f"Gagal mengirim email OTP ke {patient.email}: {str(e)}")
			mail_sent = False
	else:
		frappe.log_error(
			title="Patient OTP Dev Mode",
			message=f"Email server belum dikonfigurasi / email kosong. Kode OTP untuk {search_key} adalah: {otp_code}"
		)

	# Clear internal msgprint logs to prevent red _server_messages in API response
	if hasattr(frappe.local, "message_log"):
		frappe.local.message_log = []

	response = {
		"status": "success",
		"message": f"Kode OTP berhasil dikirimkan",
		"identifier": search_key,
		"otp_debug": otp_code
	}

	if not mail_sent:
		response["dev_note"] = "Email SMTP gagal terkirim atau belum disetup di Desk Frappe. Gunakan otp_debug untuk pengujian."

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
		SELECT name, patient_name, email, uid, mobile, dob, sex, blood_group, patient_details, custom_verification_status, custom_verification_notes
		FROM `tabPatient`
		WHERE (email IS NOT NULL AND LOWER(email) = %s)
		   OR (mobile IS NOT NULL AND mobile = %s)
		ORDER BY creation DESC
		LIMIT 1
	""", (search_key.lower(), search_key), as_dict=True)

	if not patient_list:
		frappe.throw(_("Data pasien tidak ditemukan"), frappe.DoesNotExistError)

	patient = patient_list[0]

	v_status = (patient.get("custom_verification_status") or "Approved").strip()
	if v_status in ["Pending Verification", "Pending", "Belum Diverifikasi"]:
		frappe.throw(_("Akun pasien '{0}' sedang dalam proses verifikasi berkas. Silakan tunggu konfirmasi sebelum login.").format(patient.patient_name), frappe.PermissionError)
	if v_status in ["Rejected", "Ditolak"]:
		notes = patient.get("custom_verification_notes") or "Silakan hubungi RS."
		frappe.throw(_("Pendaftaran akun pasien '{0}' ditolak oleh Admin SIMRS. Catatan: {1}").format(patient.patient_name, notes), frappe.PermissionError)

	guarantee_info = parse_patient_guarantee(patient)

	patient_dict = {
		"name": patient.name,
		"patient_name": patient.patient_name,
		"email": patient.email,
		"uid": patient.uid,
		"mobile": patient.mobile,
		"dob": str(patient.dob) if patient.dob else None,
		"sex": patient.sex,
		"blood_group": patient.blood_group,
		"patient_details": patient.patient_details
	}
	patient_dict.update(guarantee_info)

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
		"patient": patient_dict
	}

@frappe.whitelist(allow_guest=True)
def register_patient(
	name,
	nik,
	gender,
	dob,
	phone,
	email,
	mode_of_payment=None,
	bpjs_number=None,
	bpjs_referral_file=None,
	company_name=None,
	company_guarantee_file=None,
	insurance_name=None,
	insurance_card_file=None
):
	"""
	Register a new patient with Pending Verification status for Admin SIMRS approval.
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

	# Normalize mode_of_payment to match Patient custom_mode_of_payment Select field options
	mop_clean = mode_of_payment or "Cash"
	mop_lower = mop_clean.lower()
	if "bpjs" in mop_lower:
		mop_select = "BPJS"
	elif "perusahaan" in mop_lower or "company" in mop_lower or "guarantee" in mop_lower:
		mop_select = "Company Guarantee"
	elif "asuran" in mop_lower or "insur" in mop_lower:
		mop_select = "Asurance"
	else:
		mop_select = "Cash"

	# Build initial guarantee details JSON (file URLs populated after physical save)
	guarantee_info = {
		"mode_of_payment": mop_clean,
		"bpjs_number": (bpjs_number or "").strip(),
		"bpjs_referral_file": "",
		"company_name": (company_name or "").strip(),
		"company_guarantee_file": "",
		"insurance_name": (insurance_name or "").strip(),
		"insurance_card_file": "",
		"verification_status": "Pending Verification"
	}

	patient = frappe.get_doc({
		"doctype": "Patient",
		"first_name": name,
		"patient_name": name,
		"uid": nik,
		"sex": sex,
		"dob": dob,
		"mobile": phone,
		"email": email,
		"invite_user": 0,
		"custom_verification_status": "Pending Verification",
		"custom_mode_of_payment": mop_select,
		"custom_bpjs_number": (bpjs_number or "").strip(),
		"custom_bpjs_referral_file": "",
		"custom_company_name": (company_name or "").strip(),
		"custom_company_guarantee_file": "",
		"custom_insurance_name": (insurance_name or "").strip(),
		"custom_insurance_card_file": "",
		"patient_details": json.dumps(guarantee_info)
	})
	patient.insert(ignore_permissions=True)

	# Process & save uploaded Base64 files to Frappe public/files/
	saved_bpjs_file = save_patient_uploaded_file(patient.name, "custom_bpjs_referral_file", bpjs_referral_file)
	saved_company_file = save_patient_uploaded_file(patient.name, "custom_company_guarantee_file", company_guarantee_file)
	saved_insurance_file = save_patient_uploaded_file(patient.name, "custom_insurance_card_file", insurance_card_file)

	# Update Patient custom fields with real saved file URLs
	file_updates = {}
	if saved_bpjs_file:
		file_updates["custom_bpjs_referral_file"] = saved_bpjs_file
		guarantee_info["bpjs_referral_file"] = saved_bpjs_file
	if saved_company_file:
		file_updates["custom_company_guarantee_file"] = saved_company_file
		guarantee_info["company_guarantee_file"] = saved_company_file
	if saved_insurance_file:
		file_updates["custom_insurance_card_file"] = saved_insurance_file
		guarantee_info["insurance_card_file"] = saved_insurance_file

	file_updates["patient_details"] = json.dumps(guarantee_info)
	frappe.db.set_value("Patient", patient.name, file_updates)
	patient.reload()

	# Clear internal msgprint logs (e.g. 'Customer ... created and linked to Patient') to prevent red _server_messages in API response
	if hasattr(frappe.local, "message_log"):
		frappe.local.message_log = []

	return {
		"status": "pending_verification",
		"message": f"Pendaftaran rekam medis atas nama {patient.patient_name} berhasil dikirim! Silakan tunggu verifikasi oleh Admin SIMRS.",
		"patient": {
			"name": patient.name,
			"patient_name": patient.patient_name,
			"email": patient.email,
			"uid": patient.uid,
			"mobile": patient.mobile,
			"dob": str(patient.dob) if patient.dob else None,
			"sex": patient.sex,
			"verification_status": "Pending Verification"
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
	guarantee_info = parse_patient_guarantee(patient)

	patient_dict = {
		"name": patient.name,
		"patient_name": patient.patient_name,
		"email": patient.email,
		"uid": getattr(patient, "uid", None),
		"mobile": patient.mobile,
		"dob": str(patient.dob) if patient.dob else None,
		"sex": patient.sex,
		"blood_group": patient.blood_group,
		"patient_details": patient.patient_details
	}
	patient_dict.update(guarantee_info)

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
		"patient": patient_dict,
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

	# Fallback guarantee details from patient profile if not passed
	guarantee_defaults = parse_patient_guarantee(patient)
	if not mode_of_payment:
		mode_of_payment = guarantee_defaults.get("mode_of_payment") or "Cash"
	if not bpjs_number:
		bpjs_number = guarantee_defaults.get("bpjs_number") or ""
	if not insurance_name:
		insurance_name = guarantee_defaults.get("insurance_name") or ""
	if not company_name:
		company_name = guarantee_defaults.get("company_name") or ""

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
		"notes": f"Catatan: {patient_notes or '-'}\nMetode Penjamin: {mode_of_payment}\nBPJS: {bpjs_number or '-'}\nAsuransi/Company: {insurance_name or company_name or '-'}",
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

def on_patient_update(doc, method=None):
	"""
	Hook trigger ketika dokumen Patient diperbarui/disimpan di Desk Frappe.
	Mengirimkan email notifikasi ke Gmail pasien saat status verifikasi berubah menjadi Approved atau Rejected.
	"""
	if not doc.email:
		return

	# Check if custom_verification_status has changed
	status_changed = doc.has_value_changed("custom_verification_status") if hasattr(doc, "has_value_changed") else True
	if not status_changed:
		return

	v_status = (doc.custom_verification_status or "").strip()
	if v_status not in ["Approved", "Rejected", "Disetujui", "Ditolak"]:
		return

	system_name = frappe.db.get_default("system_name") or "DAU SIMRS"

	if v_status in ["Approved", "Disetujui"]:
		subject = f"[{system_name}] Selamat! Akun Pasien Anda Telah Diverifikasi"
		message = f"""
			<div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 500px; margin: 0 auto; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
				<div style="background-color: #2b6cb0; color: #ffffff; padding: 20px; text-align: center;">
					<h2 style="margin: 0; font-size: 20px;">Layanan Pasien Online</h2>
				</div>

				<div style="padding: 24px; background-color: #ffffff; color: #2d3748;">
					<div style="text-align: center; margin-bottom: 16px;">
						<span style="display: inline-block; background-color: #ebf8ff; color: #2b6cb0; font-size: 13px; font-weight: bold; padding: 6px 16px; border-radius: 6px; border: 1px dashed #3182ce;">
							✓ Akun Berhasil Diverifikasi
						</span>
					</div>

					<p style="margin-top: 0;">Halo <b>{doc.patient_name}</b>,</p>
					<p>Selamat! Pendaftaran akun rekam medis dan berkas penjamin Anda telah <b>disetujui</b> oleh Petugas Admin SIMRS. Sekarang Anda sudah dapat melakukan login dan memesan janji temu dokter.</p>

					<div style="background-color: #f7fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 14px; margin: 18px 0; font-size: 13px;">
						<table style="width: 100%; border-collapse: collapse;">
							<tr>
								<td style="padding: 3px 0; color: #718096; width: 40%;">Nama Pasien:</td>
								<td style="padding: 3px 0; font-weight: bold; color: #2d3748;">{doc.patient_name}</td>
							</tr>
							<tr>
								<td style="padding: 3px 0; color: #718096;">ID Rekam Medis:</td>
								<td style="padding: 3px 0; font-weight: bold; color: #2d3748;">{doc.name}</td>
							</tr>
							<tr>
								<td style="padding: 3px 0; color: #718096;">Metode Penjamin:</td>
								<td style="padding: 3px 0; font-weight: bold; color: #2b6cb0;">{doc.custom_mode_of_payment or 'Cash'}</td>
							</tr>
							<tr>
								<td style="padding: 3px 0; color: #718096;">Status Akun:</td>
								<td style="padding: 3px 0; font-weight: bold; color: #2b6cb0;">Disetujui / Verified</td>
							</tr>
						</table>
					</div>

					<div style="text-align: center; margin: 24px 0 12px 0;">
						<a href="http://satusehat.site:3000/auth" style="background-color: #2b6cb0; color: #ffffff; text-decoration: none; padding: 10px 24px; border-radius: 6px; font-weight: bold; font-size: 14px; display: inline-block;">
							Login Ke Aplikasi Pasien
						</a>
					</div>

					<p style="font-size: 12px; color: #718096; text-align: center; margin-top: 20px; border-top: 1px solid #edf2f7; padding-top: 14px;">
						Pesan ini dikirimkan secara otomatis oleh Sistem Informasi Manajemen Rumah Sakit (SIMRS).
					</p>
				</div>
			</div>
		"""
	elif v_status in ["Rejected", "Ditolak"]:
		subject = f"[{system_name}] Informasi Verifikasi Pendaftaran Pasien"
		notes = getattr(doc, "custom_verification_notes", None) or "Berkas belum sesuai. Silakan hubungi customer service RS."
		message = f"""
			<div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 500px; margin: 0 auto; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
				<div style="background-color: #e53e3e; color: #ffffff; padding: 20px; text-align: center;">
					<h2 style="margin: 0; font-size: 20px;">Layanan Pasien Online</h2>
				</div>

				<div style="padding: 24px; background-color: #ffffff; color: #2d3748;">
					<div style="text-align: center; margin-bottom: 16px;">
						<span style="display: inline-block; background-color: #fff5f5; color: #c53030; font-size: 13px; font-weight: bold; padding: 6px 16px; border-radius: 6px; border: 1px dashed #e53e3e;">
							✕ Verifikasi Belum Disetujui
						</span>
					</div>

					<p style="margin-top: 0;">Halo <b>{doc.patient_name}</b>,</p>
					<p>Mohon maaf, pendaftaran akun rekam medis / berkas penjamin Anda <b>belum disetujui</b> oleh Petugas Admin SIMRS.</p>

					<div style="background-color: #fff5f5; border: 1px solid #fed7d7; border-radius: 6px; padding: 14px; margin: 18px 0; font-size: 13px;">
						<div style="font-weight: bold; color: #9b2c2c; margin-bottom: 4px;">Catatan Petugas RS:</div>
						<div style="color: #742a2a; font-style: italic;">"{notes}"</div>
					</div>

					<p style="font-size: 13px; color: #718096; text-align: center; margin-top: 18px;">
						Silakan melakukan pendaftaran ulang dengan melengkapi berkas yang sesuai atau hubungi loket pendaftaran RS.
					</p>
				</div>
			</div>
		"""

	try:
		frappe.sendmail(
			recipients=[doc.email],
			subject=subject,
			message=message,
			now=False
		)
		# Flush queue immediately so email is sent right away without waiting for background bench worker
		from frappe.email.queue import flush
		flush()
	except Exception as e:
		frappe.log_error(
			title="Patient Mail Verification Error",
			message=f"Gagal mengirim email notifikasi verifikasi ke {doc.email}: {str(e)}"
		)

	if hasattr(frappe.local, "message_log"):
		frappe.local.message_log = []
