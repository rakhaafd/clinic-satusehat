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
		"mode_of_payment": getattr(patient, "custom_mode_of_payment", None) or "",
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
	mop_clean = mode_of_payment or ""
	mop_lower = mop_clean.lower()
	if "bpjs" in mop_lower:
		mop_select = "BPJS"
	elif "perusahaan" in mop_lower or "company" in mop_lower or "guarantee" in mop_lower:
		mop_select = "Company Guarantee"
	elif "asuran" in mop_lower or "insur" in mop_lower:
		mop_select = "Insurance"
	elif "cash" in mop_lower:
		mop_select = "Cash"
	else:
		mop_select = ""

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
		"custom_verification_status": "Approved",
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
		"status": "success",
		"message": f"Pendaftaran rekam medis atas nama {patient.patient_name} berhasil!",
		"patient": {
			"name": patient.name,
			"patient_name": patient.patient_name,
			"email": patient.email,
			"uid": patient.uid,
			"mobile": patient.mobile,
			"dob": str(patient.dob) if patient.dob else None,
			"sex": patient.sex,
			"verification_status": "Approved"
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

def get_appointment_doctor_status(app):
	"""
	Mengambil status_doctor berdasarkan flow:
	Patient Encounter -> cari Patient Appointment yang di link -> ambil field dari Queue Registration
	"""
	app_id = app.name if hasattr(app, "name") else (app.get("name") if isinstance(app, dict) else str(app))

	enc = frappe.db.get_value("Patient Encounter", {"appointment": app_id}, "name")
	if enc:
		status_doc = frappe.db.get_value("Queue Registration", {"reference_encounter": enc}, "status_doctor")
		if status_doc and str(status_doc).strip():
			return str(status_doc).strip()

	return "Pending"

@frappe.whitelist(allow_guest=True)
def get_patient_appointments(token=None):
	"""
	API: Mengambil daftar riwayat janji temu pasien saat ini dari Doctype Patient Appointment berdasarkan token session.
	Status 'COMPLETED' (Selesai) HANYA berlaku ketika status_doctor == 'Completed'.
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
		doc_status = get_appointment_doctor_status(app)


		# Requirement: Status Selesai HANYA ketika status_doctor == Completed
		if doc_status.lower() in ["completed", "selesai"] or status_lower in ["completed"]:
			fe_status = "COMPLETED"
		elif status_lower in ["cancelled", "dibatalkan"] or doc_status.lower() in ["cancelled", "dibatalkan"]:
			fe_status = "CANCELLED"
		else:
			fe_status = "UPCOMING"

		patients_ahead = 0
		if fe_status == "UPCOMING" and app.practitioner and app.appointment_date:
			earlier_apps = frappe.db.get_all(
				"Patient Appointment",
				filters={
					"practitioner": app.practitioner,
					"appointment_date": app.appointment_date,
					"creation": ["<", app.creation],
					"status": ["not in", ["Cancelled", "Dibatalkan"]]
				},
				fields=["name"]
			)
			for earlier_app in earlier_apps:
				e_status = get_appointment_doctor_status(earlier_app.name)
				if e_status not in ["Completed", "Cancelled", "Selesai", "Dibatalkan"]:
					patients_ahead += 1

		if doc_status == "Called":
			queue_msg = "Giliran Anda! Silakan masuk ke ruang periksa dokter."
		elif doc_status == "Completed":
			queue_msg = "Pemeriksaan dokter telah selesai."
		elif patients_ahead > 0:
			queue_msg = f"Kurang {patients_ahead} pasien lagi sebelum antrian Anda dipanggil dokter."
		else:
			queue_msg = "Anda adalah antrian berikutnya. Bersiaplah dipanggil dokter."

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
			"statusDoctor": doc_status,
			"patientsAhead": patients_ahead,
			"queueMessage": queue_msg,
			"qrCodeValue": app.name,
			"creation": str(app.creation)
		})

	return {
		"status": "success",
		"appointments": formatted_list
	}

@frappe.whitelist(allow_guest=True)
def get_patient_active_queue(token=None):
	"""
	API khusus untuk menu Antrian di FE untuk memantau sisa antrean dan status dipanggil dokter secara real-time.
	"""
	payload = verify_token_payload(token)
	patient_id = payload.get("patient_id")

	# Fetch all non-cancelled appointments for patient to find the active one
	candidate_apps = frappe.db.get_all(
		"Patient Appointment",
		filters={
			"patient": patient_id,
			"status": ["not in", ["Cancelled", "Dibatalkan"]]
		},
		fields=[
			"name", "patient_name", "practitioner", "practitioner_name",
			"department", "company", "appointment_date", "appointment_time",
			"mode_of_payment", "status", "creation"
		],
		order_by="creation asc"
	)

	active_app = None
	for candidate in candidate_apps:
		status_doc = get_appointment_doctor_status(candidate)
		if status_doc not in ["Completed", "Cancelled", "Selesai", "Dibatalkan"]:
			active_app = candidate
			break

	if not active_app:
		return {
			"status": "success",
			"has_active_queue": False,
			"message": "Tidak ada antrian aktif saat ini."
		}

	app = active_app
	from clinic_satusehat.api.hospital_search import format_doctor_data

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

	# Count patients ahead
	patients_ahead = 0
	earlier_apps = frappe.db.get_all(
		"Patient Appointment",
		filters={
			"practitioner": app.practitioner,
			"appointment_date": app.appointment_date,
			"creation": ["<", app.creation],
			"status": ["not in", ["Cancelled", "Dibatalkan"]]
		},
		fields=["name"]
	)
	for earlier_app in earlier_apps:
		e_status = get_appointment_doctor_status(earlier_app.name)
		if e_status not in ["Completed", "Cancelled", "Selesai", "Dibatalkan"]:
			patients_ahead += 1

	status_doc = get_appointment_doctor_status(app)

	if status_doc in ["Called", "Dipanggil"]:
		queue_msg = "Giliran Anda! Silakan masuk"
	elif patients_ahead > 0:
		queue_msg = f"Sisa {patients_ahead} pasien lagi"
	else:
		queue_msg = "Antrian berikutnya"

	try:
		doc_num = int(app.name.split("-")[-1])
		queue_num = f"A-{doc_num:03d}"
	except Exception:
		queue_num = "A-001"

	return {
		"status": "success",
		"has_active_queue": True,
		"queue": {
			"id": app.name,
			"bookingCode": app.name,
			"queueNumber": queue_num,
			"doctor": doctor_data,
			"appointmentDate": str(app.appointment_date),
			"appointmentTime": str(app.appointment_time)[:5] if app.appointment_time else "09:00",
			"polyClinic": app.department or doctor_data.get("poly", "Penyakit Dalam"),
			"paymentMethod": app.mode_of_payment or "Tunai / Cash",
			"statusDoctor": status_doc,
			"patientsAhead": patients_ahead,
			"queueMessage": queue_msg,
			"creation": str(app.creation)
		}
	}

def on_queue_status_update(doc, method=None):
	"""
	Hook trigger ketika status_doctor pasien diubah di Desk Frappe:
	Jika status_doctor == 'Completed', otomatis ubah status_doctor pasien berikutnya dalam antrean menjadi 'Called'.
	"""
	if doc.doctype != "Queue Registration":
		return

	v_status = (getattr(doc, "status_doctor", None) or "").strip()
	if v_status not in ["Completed", "Selesai"]:
		return

	if not getattr(doc, "appointment", None):
		return

	app = frappe.get_doc("Patient Appointment", doc.appointment)
	if not app.practitioner or not app.appointment_date:
		return

	# Search next patient in queue for the same doctor & date
	next_patients = frappe.db.get_all(
		"Patient Appointment",
		filters={
			"practitioner": app.practitioner,
			"appointment_date": app.appointment_date,
			"name": ["!=", app.name],
			"creation": [">", app.creation],
			"status": ["not in", ["Cancelled", "Dibatalkan"]]
		},
		fields=["name", "creation"],
		order_by="creation asc"
	)

	for next_p in next_patients:
		e_status = get_appointment_doctor_status(next_p.name)
		if e_status not in ["Completed", "Cancelled", "Selesai", "Dibatalkan"]:
			# Set this next queue registration to Called
			enc_name = frappe.db.get_value("Patient Encounter", {"appointment": next_p.name}, "name")
			if enc_name:
				qr_name = frappe.db.get_value("Queue Registration", {"reference_encounter": enc_name}, "name")
				if qr_name:
					frappe.db.set_value("Queue Registration", qr_name, "status_doctor", "Called")
					frappe.db.commit()
			break

@frappe.whitelist(allow_guest=True)
def update_patient_guarantee(
	token=None,
	mode_of_payment=None,
	insurance_name=None,
	insurance_card_file=None,
	company_name=None,
	company_guarantee_file=None,
	bpjs_number=None,
	bpjs_referral_file=None
):
	"""
	API: Memperbarui data penjamin pasien (dipanggil langsung setelah modal)
	"""
	if not token:
		frappe.throw(_("Token autentikasi pasien tidak ditemukan"), frappe.PermissionError)

	payload = verify_token_payload(token)
	patient_id = payload.get("patient_id")
	patient = frappe.get_doc("Patient", patient_id)

	guarantee_defaults = parse_patient_guarantee(patient)
	
	mop_clean = mode_of_payment or ""
	mop_lower = mop_clean.lower()
	if "bpjs" in mop_lower:
		mop_select = "BPJS"
	elif "perusahaan" in mop_lower or "company" in mop_lower or "guarantee" in mop_lower:
		mop_select = "Company Guarantee"
	elif "asuran" in mop_lower or "insur" in mop_lower:
		mop_select = "Insurance"
	elif "cash" in mop_lower:
		mop_select = "Cash"
	else:
		mop_select = ""

	guarantee_defaults.update({
		"mode_of_payment": mop_clean,
		"bpjs_number": (bpjs_number or "").strip(),
		"company_name": (company_name or "").strip(),
		"insurance_name": (insurance_name or "").strip(),
	})

	file_updates = {
		"custom_mode_of_payment": mop_select,
		"custom_bpjs_number": guarantee_defaults["bpjs_number"],
		"custom_company_name": guarantee_defaults["company_name"],
		"custom_insurance_name": guarantee_defaults["insurance_name"]
	}

	if bpjs_referral_file:
		saved_file = save_patient_uploaded_file(patient.name, "custom_bpjs_referral_file", bpjs_referral_file)
		if saved_file:
			file_updates["custom_bpjs_referral_file"] = saved_file
			guarantee_defaults["bpjs_referral_file"] = saved_file

	if company_guarantee_file:
		saved_file = save_patient_uploaded_file(patient.name, "custom_company_guarantee_file", company_guarantee_file)
		if saved_file:
			file_updates["custom_company_guarantee_file"] = saved_file
			guarantee_defaults["company_guarantee_file"] = saved_file

	if insurance_card_file:
		saved_file = save_patient_uploaded_file(patient.name, "custom_insurance_card_file", insurance_card_file)
		if saved_file:
			file_updates["custom_insurance_card_file"] = saved_file
			guarantee_defaults["insurance_card_file"] = saved_file

	file_updates["patient_details"] = json.dumps(guarantee_defaults)
	frappe.db.set_value("Patient", patient.name, file_updates)
	patient.reload()

	return {
		"status": "success",
		"message": "Data penjamin berhasil disimpan ke profil pasien",
		"patient_details": guarantee_defaults
	}

@frappe.whitelist(allow_guest=True)
def create_patient_appointment(
	token=None,
	practitioner=None,
	appointment_date=None,
	appointment_time=None,
	mode_of_payment=None,
	insurance_name=None,
	insurance_card_file=None,
	company_name=None,
	company_guarantee_file=None,
	bpjs_number=None,
	bpjs_referral_file=None,
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

	# Validation: Cannot book for past dates or past time if today
	current_date = frappe.utils.nowdate()
	if appointment_date < current_date:
		frappe.throw(_("Tidak bisa mendaftar janji temu untuk tanggal yang sudah terlewat."), frappe.ValidationError)
	elif appointment_date == current_date:
		# compare 'HH:MM:00'
		if time_clean + ":00" <= frappe.utils.nowtime():
			frappe.throw(_("Sesi berobat jam {0} sudah terlewat. Silakan pilih jam/sesi lain.").format(time_clean), frappe.ValidationError)

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
