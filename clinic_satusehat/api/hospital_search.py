import frappe
from frappe import _

@frappe.whitelist(allow_guest=True)
def get_hospitals_and_locations():
	"""
	API 1: Mengambil daftar Rumah Sakit (Company), Lokasi, dan Spesialisasi (Medical Department)
	untuk mengisi opsi filter di React Frontend saat pertama kali dimuat.
	"""
	fields = ["name", "company_name", "country"]
	if frappe.db.has_column("Company", "custom_city"):
		fields.append("custom_city")

	hospitals = frappe.db.get_all(
		"Company",
		fields=fields,
		order_by="company_name asc"
	)

	departments_raw = frappe.db.get_all(
		"Medical Department",
		fields=["name"],
		order_by="name asc"
	)
	departments = [{"name": d["name"], "department_name": d["name"]} for d in departments_raw]

	locations = list(set([h.get("custom_city") or h.get("country") for h in hospitals if (h.get("custom_city") or h.get("country"))]))

	return {
		"status": "success",
		"data": {
			"hospitals": hospitals,
			"departments": departments,
			"locations": sorted(locations)
		}
	}


@frappe.whitelist(allow_guest=True)
def get_departments_by_company(company=None):
	"""
	API 2: Mengambil daftar Spesialisasi (Medical Department) yang HANYA ADA
	di Rumah Sakit (Company) tertentu secara dinamis berdasarkan dokter yang praktek.
	"""
	if not company:
		departments_raw = frappe.db.get_all("Medical Department", fields=["name"], order_by="name asc")
		return {"status": "success", "departments": [{"name": d["name"], "department_name": d["name"]} for d in departments_raw]}

	# Search Healthcare Practitioner where hospital matches company, or service unit company matches
	dept_names = set()

	# 1. Check direct hospital match on Healthcare Practitioner
	if frappe.db.has_column("Healthcare Practitioner", "hospital"):
		matched_by_hosp = frappe.db.get_all(
			"Healthcare Practitioner",
			filters={"hospital": company},
			pluck="department"
		)
		dept_names.update([d for d in matched_by_hosp if d])

	# 2. Check Service Units associated with the Company
	service_units = frappe.db.get_all("Healthcare Service Unit", filters={"company": company}, pluck="name")
	if service_units:
		matched_by_su = frappe.db.sql_list("""
			SELECT DISTINCT parent.department
			FROM `tabPractitioner Service Unit Schedule` child
			JOIN `tabHealthcare Practitioner` parent ON child.parent = parent.name
			WHERE child.service_unit IN %s AND parent.department IS NOT NULL
		""", (tuple(service_units),))
		dept_names.update([d for d in matched_by_su if d])

	# Fallback: If no specific practitioner link exists yet, return all departments
	if not dept_names:
		departments_raw = frappe.db.get_all("Medical Department", fields=["name"], order_by="name asc")
		return {"status": "success", "departments": [{"name": d["name"], "department_name": d["name"]} for d in departments_raw]}

	departments_raw = frappe.db.get_all(
		"Medical Department",
		filters={"name": ["in", list(dept_names)]},
		fields=["name"],
		order_by="name asc"
	)
	departments = [{"name": d["name"], "department_name": d["name"]} for d in departments_raw]

	return {
		"status": "success",
		"company": company,
		"departments": departments
	}


DAY_TRANSLATIONS = {
	"Monday": {"long": "Senin", "short": "Sen"},
	"Tuesday": {"long": "Selasa", "short": "Sel"},
	"Wednesday": {"long": "Rabu", "short": "Rab"},
	"Thursday": {"long": "Kamis", "short": "Kam"},
	"Friday": {"long": "Jumat", "short": "Jum"},
	"Saturday": {"long": "Sabtu", "short": "Sab"},
	"Sunday": {"long": "Minggu", "short": "Min"}
}
DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

def format_time_str(val):
	if not val:
		return "00:00"
	s = str(val).strip()
	parts = s.split(":")
	if len(parts) >= 2:
		hh = parts[0].zfill(2)
		mm = parts[1].zfill(2)
		return f"{hh}:{mm}"
	return s[:5]

def get_doctor_schedules(doctor_name):
	# Fetch schedules linked in Practitioner Service Unit Schedule
	schedules = frappe.db.get_all(
		"Practitioner Service Unit Schedule",
		filters={"parent": doctor_name},
		pluck="schedule"
	)

	if not schedules:
		return {
			"availableDays": ["Sen", "Sel", "Rab", "Kam", "Jum"],
			"practiceSchedules": [
				{"day": "Senin - Kamis", "time": "09.00 - 13.00"},
				{"day": "Jumat", "time": "09.00 - 11.30"}
			],
			"availableSlots": ["08:30", "09:00", "09:30", "10:00", "10:30", "11:00", "13:30", "14:00"]
		}

	# Fetch slots from Healthcare Schedule Time Slot grouped by day
	slots = frappe.db.sql("""
		SELECT day, min(from_time) as min_from, max(to_time) as max_to
		FROM `tabHealthcare Schedule Time Slot`
		WHERE parent IN %s
		GROUP BY day
	""", (tuple(schedules),), as_dict=True)

	# Fetch all individual starting time slots for availableSlots list
	all_slots_raw = frappe.db.sql("""
		SELECT DISTINCT from_time
		FROM `tabHealthcare Schedule Time Slot`
		WHERE parent IN %s
		ORDER BY from_time ASC
	""", (tuple(schedules),), as_dict=True)

	available_slots = []
	for s in all_slots_raw:
		formatted_t = format_time_str(s.get("from_time"))
		if formatted_t not in available_slots:
			available_slots.append(formatted_t)

	slots_by_day = {s["day"]: s for s in slots}
	available_days = []
	practice_schedules = []

	for day_en in DAY_ORDER:
		if day_en in slots_by_day:
			d_data = slots_by_day[day_en]
			d_info = DAY_TRANSLATIONS.get(day_en, {"long": day_en, "short": day_en[:3]})
			available_days.append(d_info["short"])

			from_t = format_time_str(d_data["min_from"]).replace(":", ".")
			to_t = format_time_str(d_data["max_to"]).replace(":", ".")
			time_range = f"{from_t} - {to_t}"

			practice_schedules.append({
				"day": d_info["long"],
				"time": time_range
			})

	return {
		"availableDays": available_days if available_days else ["Sen", "Sel", "Rab", "Kam", "Jum"],
		"practiceSchedules": practice_schedules if practice_schedules else [{"day": "Senin - Jumat", "time": "09.00 - 12.00"}],
		"availableSlots": available_slots if available_slots else ["08:30", "09:00", "09:30", "10:00", "10:30", "11:00"]
	}

def format_doctor_data(doc):
	hosp_name = getattr(doc, "hospital", None) or "RS Andalan"
	dept = doc.get("department") or "Penyakit Dalam"
	desc = doc.get("custom_description") or ""

	image_url = doc.get("image")
	sched_info = get_doctor_schedules(doc.name)

	return {
		"id": doc.name,
		"name": doc.practitioner_name,
		"specialty": f"Spesialis {dept}",
		"subSpecialty": f"Kualifikasi & Perawatan {dept}",
		"poly": dept,
		"rating": 4.9,
		"reviewCount": 125,
		"experienceYears": 10,
		"avatarUrl": image_url or "https://images.unsplash.com/photo-1622253692010-333f2da6031d?w=400&auto=format&fit=crop&q=80",
		"hospital": hosp_name,
		"availableDays": sched_info["availableDays"],
		"todayAvailable": True,
		"nextAvailableSlot": "09:00 - 12:00 WIB",
		"fee": 150000,
		"availableSlots": sched_info["availableSlots"],
		"practiceSchedules": sched_info["practiceSchedules"],
		"description": desc,
		"image": image_url,
		"mobile": doc.get("mobile_phone")
	}

@frappe.whitelist(allow_guest=True)
def search_doctors(search_text=None, company=None, department=None, location=None):
	"""
	API 3: Pencarian Dokter utama (Filter berantai: Nama Dokter, Rumah Sakit, Spesialisasi, Lokasi)
	"""
	filters = {}

	if department and department != "all":
		filters["department"] = department
	if search_text:
		filters["practitioner_name"] = ["like", f"%{search_text}%"]
	if company and company != "all" and frappe.db.has_column("Healthcare Practitioner", "hospital"):
		filters["hospital"] = company

	doctors = frappe.db.get_all(
		"Healthcare Practitioner",
		filters=filters,
		fields=["name", "practitioner_name", "department", "image", "mobile_phone", "custom_description"],
		order_by="practitioner_name asc"
	)

	result = [format_doctor_data(doc) for doc in doctors]

	return {
		"status": "success",
		"count": len(result),
		"doctors": result
	}

@frappe.whitelist(allow_guest=True)
def get_doctor_detail(doctor_id=None):
	"""
	API 4: Mengambil detail 1 dokter berdasarkan ID (name)
	"""
	if not doctor_id:
		frappe.throw(_("ID Dokter wajib diisi"), frappe.MandatoryError)

	doc = frappe.db.get_value(
		"Healthcare Practitioner",
		doctor_id,
		["name", "practitioner_name", "department", "image", "mobile_phone", "custom_description"],
		as_dict=True
	)

	if not doc:
		frappe.throw(_("Dokter tidak ditemukan"), frappe.DoesNotExistError)

	return {
		"status": "success",
		"doctor": format_doctor_data(doc)
	}

@frappe.whitelist(allow_guest=True)
def get_payment_methods():
	"""
	API 5: Mengambil daftar Metode Pembayaran (Mode of Payment) dari Frappe
	"""
	modes = frappe.db.get_all(
		"Mode of Payment",
		filters={"enabled": 1},
		fields=["name", "mode_of_payment", "type"],
		order_by="name asc"
	)

	return {
		"status": "success",
		"payment_methods": modes
	}

@frappe.whitelist(allow_guest=True)
def get_booked_slots(practitioner=None, appointment_date=None):
	"""
	API 6: Mengambil daftar jam / slot berobat yang SUDAH di-booking orang lain
	untuk dokter & tanggal berobat tertentu.
	"""
	if not practitioner or not appointment_date:
		return {"status": "success", "booked_slots": []}

	try:
		formatted_date = str(frappe.utils.getdate(appointment_date))
	except Exception:
		formatted_date = str(appointment_date)

	booked = frappe.db.get_all(
		"Patient Appointment",
		filters={
			"practitioner": practitioner,
			"appointment_date": formatted_date,
			"status": ["not in", ["Cancelled", "Dibatalkan"]]
		},
		pluck="appointment_time"
	)

	formatted_slots = []
	for b in booked:
		if b:
			time_clean = format_time_str(b)
			if time_clean not in formatted_slots:
				formatted_slots.append(time_clean)

	return {
		"status": "success",
		"practitioner": practitioner,
		"appointment_date": formatted_date,
		"booked_slots": formatted_slots
	}
