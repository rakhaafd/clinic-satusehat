import frappe
from frappe import _
import random
import jwt
import datetime

# Secret key for JWT encoding/decoding (minimum 32 bytes)
DEFAULT_JWT_SECRET = "clinic_satusehat_patient_auth_secret_key_2026_v1"

def get_jwt_secret():
	return frappe.conf.get("jwt_secret") or DEFAULT_JWT_SECRET

def verify_token_payload():
	"""
	Helper to verify Authorization header token and return decoded payload.
	"""
	auth_header = frappe.get_request_header("Authorization")
	if not auth_header or not auth_header.startswith("Bearer "):
		frappe.throw(_("Token autentikasi pasien tidak ditemukan di header"), frappe.PermissionError)
	
	token = auth_header.split(" ")[1]
	try:
		payload = jwt.decode(token, get_jwt_secret(), algorithms=["HS256"])
		return payload
	except jwt.ExpiredSignatureError:
		frappe.throw(_("Sesi login telah kedaluwarsa, silakan login kembali"), frappe.PermissionError)
	except jwt.InvalidTokenError:
		frappe.throw(_("Token autentikasi tidak valid"), frappe.PermissionError)

@frappe.whitelist(allow_guest=True)
def send_patient_otp(email):
	"""
	Generate and send 6-digit OTP to patient's registered email.
	"""
	if not email:
		frappe.throw(_("Email wajib diisi"), frappe.MandatoryError)

	email = email.strip().lower()

	# Search Patient by email
	patient = frappe.db.get_value(
		"Patient",
		{"email": email},
		["name", "patient_name", "email", "mobile"],
		as_dict=True
	)

	if not patient:
		frappe.throw(_("Pasien dengan email '{0}' tidak ditemukan di sistem").format(email), frappe.DoesNotExistError)

	# Generate 6-digit OTP
	otp_code = str(random.randint(100000, 999999))

	# Save OTP to Redis cache (5 minutes expiration = 300s)
	cache_key = f"patient_otp:{email}"
	frappe.cache().set_value(cache_key, otp_code, expires_in_sec=300)

	# Send OTP email
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

	# Check if default outgoing Email Account is configured in Frappe
	has_outgoing_account = frappe.db.exists("Email Account", {"default_outgoing": 1, "enable_outgoing": 1})

	if has_outgoing_account:
		try:
			frappe.sendmail(
				recipients=[email],
				subject=subject,
				message=message,
				now=True
			)
		except Exception as e:
			frappe.log_error(f"Gagal mengirim email OTP ke {email}: {str(e)}", "Patient OTP Mail Error")
	else:
		# Log to Frappe error log for dev testing when SMTP is not configured
		frappe.log_error(
			f"Email server belum dikonfigurasi. Kode OTP untuk {email} adalah: {otp_code}",
			"Patient OTP Dev Mode"
		)

	# Clear internal msgprint logs to prevent red _server_messages in API response
	if hasattr(frappe.local, "message_log"):
		frappe.local.message_log = []

	response = {
		"status": "success",
		"message": f"Kode OTP berhasil dikirimkan ke email {email}",
		"email": email
	}

	if not has_outgoing_account:
		response["dev_note"] = "Email Account SMTP belum disetup di Desk Frappe. Gunakan otp_debug untuk pengujian lokal."
		response["otp_debug"] = otp_code

	return response

@frappe.whitelist(allow_guest=True)
def verify_patient_otp(email, otp_code):
	"""
	Verify 6-digit OTP and return JWT login token + patient info.
	"""
	if not email or not otp_code:
		frappe.throw(_("Email dan Kode OTP wajib diisi"), frappe.MandatoryError)

	email = email.strip().lower()
	otp_code = str(otp_code).strip()

	cache_key = f"patient_otp:{email}"
	saved_otp = frappe.cache().get_value(cache_key)

	if not saved_otp:
		frappe.throw(_("Kode OTP telah kedaluwarsa atau belum diminta. Silakan minta OTP baru."), frappe.AuthenticationError)

	if str(saved_otp) != otp_code:
		frappe.throw(_("Kode OTP yang Anda masukkan salah"), frappe.AuthenticationError)

	# OTP is valid -> delete from Redis cache to prevent reuse
	frappe.cache().delete_value(cache_key)

	# Retrieve Patient details
	patient = frappe.db.get_value(
		"Patient",
		{"email": email},
		["name", "patient_name", "email", "uid", "mobile", "dob", "sex", "blood_group"],
		as_dict=True
	)

	if not patient:
		frappe.throw(_("Data pasien tidak ditemukan"), frappe.DoesNotExistError)

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
def get_patient_profile():
	"""
	Get profile information of currently authenticated patient using JWT Token.
	"""
	payload = verify_token_payload()
	patient_id = payload.get("patient_id")

	patient = frappe.get_doc("Patient", patient_id)
	
	# Fetch active registrations or queues
	active_registrations = frappe.db.get_all(
		"Patient Registration",
		filters={"patient": patient_id, "docstatus": ["<", 2]},
		fields=["name", "appointment_date", "appointment_time", "department", "practitioner", "docstatus"],
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
