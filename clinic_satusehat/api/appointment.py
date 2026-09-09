import frappe

@frappe.whitelist()
def get_practitioners_by_department(department=None):
	"""
	Mendapatkan daftar Healthcare Practitioner yang difilter berdasarkan Medical Department.
	"""
	filters = {}
	if department:
		filters["department"] = department

	practitioners = frappe.get_all(
		"Healthcare Practitioner",
		filters=filters,
		fields=["name", "practitioner_name", "department", "mobile_phone"]
	)
	return {"status": "success", "data": practitioners}


@frappe.whitelist()
def get_practitioner_available_slots(practitioner, date):
	"""
	Mengecek ketersediaan slot waktu (time_slots) dokter pada tanggal tertentu berdasarkan Practitioner Schedule.
	"""
	if not frappe.db.exists("Healthcare Practitioner", practitioner):
		frappe.throw(f"Practitioner {practitioner} tidak ditemukan.")

	# Convert tanggal ke nama hari dalam Bahasa Inggris (Monday, Tuesday, Wednesday, dst)
	date_obj = frappe.utils.getdate(date)
	day_of_week = date_obj.strftime("%A")

	prac_doc = frappe.get_doc("Healthcare Practitioner", practitioner)
	
	configured_days = set()
	day_slots = []

	# Ambil semua schedule milik dokter (bisa dari field 'schedules' atau 'practitioner_schedules')
	schedules_list = prac_doc.get("schedules") or prac_doc.get("practitioner_schedules") or []
	for item in schedules_list:
		schedule_name = getattr(item, "schedule", None) or getattr(item, "practitioner_schedule", None)
		if not schedule_name or not frappe.db.exists("Practitioner Schedule", schedule_name):
			continue

		sched_doc = frappe.get_doc("Practitioner Schedule", schedule_name)
		for slot in (sched_doc.get("time_slots") or []):
			if slot.day:
				configured_days.add(slot.day)
			if slot.day == day_of_week:
				# Format string HH:MM:SS
				from_time_str = str(slot.from_time).strip()
				if len(from_time_str) == 5:
					from_time_str += ":00"
				to_time_str = str(slot.to_time).strip()
				if len(to_time_str) == 5:
					to_time_str += ":00"

				day_slots.append({
					"schedule_name": sched_doc.name,
					"day": slot.day,
					"from_time": from_time_str,
					"to_time": to_time_str
				})

	# Ambil daftar janji temu yang sudah terbooking di tanggal tersebut
	booked_appointments = frappe.get_all(
		"Patient Appointment",
		filters={
			"practitioner": practitioner,
			"appointment_date": date,
			"status": ["in", ["Open", "Scheduled", "Confirmed"]]
		},
		fields=["name", "appointment_time", "status"]
	)

	# Buat set jam yang sudah terisi untuk matching cepat
	booked_times = {str(b["appointment_time"]).strip(): b["name"] for b in booked_appointments}

	# Tandai setiap time_slot apakah available atau sudah terisi
	processed_slots = []
	for s in day_slots:
		slot_time = s["from_time"]
		is_booked = slot_time in booked_times or (len(slot_time) == 8 and slot_time[:5] in [t[:5] for t in booked_times])
		processed_slots.append({
			"from_time": s["from_time"],
			"to_time": s["to_time"],
			"is_available": not is_booked,
			"booked_by_appointment": booked_times.get(slot_time) if is_booked else None
		})

	has_schedule = len(processed_slots) > 0
	message = (
		f"Jadwal tersedia untuk hari {day_of_week} ({date})."
		if has_schedule
		else f"Dokter {prac_doc.practitioner_name} tidak memiliki jadwal praktek pada hari {day_of_week} ({date}). Hari praktek tersedia: {list(configured_days)}."
	)

	return {
		"status": "success",
		"practitioner": practitioner,
		"practitioner_name": prac_doc.practitioner_name,
		"date": str(date),
		"day_of_week": day_of_week,
		"has_schedule_on_this_day": has_schedule,
		"practice_days": list(configured_days),
		"time_slots": processed_slots,
		"message": message
	}
