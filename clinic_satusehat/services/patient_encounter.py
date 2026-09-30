# Copyright (c) 2026, Rakha and contributors
# For license information, please see license.txt

import frappe


def before_patient_encounter_validate(doc, method=None):
	"""
	Auto-populates missing mandatory fields on Patient Encounter from
	Patient Registration or Patient Appointment if passed via API or form.
	"""
	# Handle alias healthcare_practitioner if passed in payload
	practitioner = doc.get("practitioner") or doc.get("healthcare_practitioner") or getattr(doc, "healthcare_practitioner", None) or getattr(doc, "practitioner", None)
	if practitioner:
		doc.practitioner = practitioner
		setattr(doc, "practitioner", practitioner)

	# Fetch from patient_registration if present
	patient_reg = doc.get("patient_registration") or getattr(doc, "patient_registration", None)
	if patient_reg:
		pr = frappe.db.get_value(
			"Patient Registration",
			patient_reg,
			[
				"patient",
				"patient_name",
				"patient_sex",
				"patient_age",
				"inpatient_record",
				"company",
				"department",
				"appointment_date",
				"appointment_time",
			],
			as_dict=True,
		)
		if pr:
			if not doc.get("patient"):
				doc.patient = pr.get("patient")
			if not doc.get("patient_name"):
				doc.patient_name = pr.get("patient_name")
			if not doc.get("patient_sex"):
				doc.patient_sex = pr.get("patient_sex")
			if not doc.get("patient_age"):
				doc.patient_age = pr.get("patient_age")
			if not doc.get("inpatient_record"):
				doc.inpatient_record = pr.get("inpatient_record")
			if not doc.get("company"):
				doc.company = pr.get("company")
			if not doc.get("medical_department"):
				doc.medical_department = pr.get("department")
			if not doc.get("encounter_date"):
				doc.encounter_date = pr.get("appointment_date")
			if not doc.get("encounter_time"):
				doc.encounter_time = pr.get("appointment_time")

	# Fetch from appointment if present
	elif doc.get("appointment"):
		app = frappe.db.get_value(
			"Patient Appointment",
			doc.get("appointment"),
			[
				"patient",
				"patient_name",
				"patient_sex",
				"patient_age",
				"inpatient_record",
				"company",
				"department",
				"appointment_date",
				"appointment_time",
				"practitioner",
			],
			as_dict=True,
		)
		if app:
			# Validasi: Encounter hanya bisa dibuat pada Hari H Appointment
			if str(app.get("appointment_date")) != frappe.utils.nowdate():
				frappe.throw(
					frappe._("Anjungan hanya dapat dibuat pada tanggal janji temu: {0}").format(app.get("appointment_date")),
					frappe.ValidationError
				)

			if not doc.get("patient"):
				doc.patient = app.get("patient")
			if not doc.get("patient_name"):
				doc.patient_name = app.get("patient_name")
			if not doc.get("patient_sex"):
				doc.patient_sex = app.get("patient_sex")
			if not doc.get("patient_age"):
				doc.patient_age = app.get("patient_age")
			if not doc.get("inpatient_record"):
				doc.inpatient_record = app.get("inpatient_record")
			if not doc.get("company"):
				doc.company = app.get("company")
			if not doc.get("medical_department"):
				doc.medical_department = app.get("department")
			if not doc.get("encounter_date"):
				doc.encounter_date = app.get("appointment_date")
			if not doc.get("encounter_time"):
				doc.encounter_time = app.get("appointment_time")
			if not doc.get("practitioner"):
				doc.practitioner = app.get("practitioner")


def on_patient_encounter_save(doc, method=None):
	"""
	Automatically creates or updates Queue Registration for Patient Encounter.
	"""
	app_id = getattr(doc, "appointment", None)

	qr_name = frappe.db.get_value("Queue Registration", {"reference_encounter": doc.name})

	if not qr_name:
		new_status = "Completed" if doc.docstatus == 1 else "Waiting"
		qr = frappe.get_doc({
			"doctype": "Queue Registration",
			"reference_encounter": doc.name,
			"patient": doc.patient,
			"patient_name": doc.patient_name,
			"appointment": app_id,
			"status_nurse": "Waiting",
			"status_doctor": new_status
		})
		qr.insert(ignore_permissions=True)
	else:
		updates = {
			"patient": doc.patient,
			"patient_name": doc.patient_name,
			"appointment": app_id
		}
		
		# Hanya ubah status_doctor secara otomatis jika encounter di submit (Completed)
		if doc.docstatus == 1:
			updates["status_doctor"] = "Completed"
			
		frappe.db.set_value("Queue Registration", qr_name, updates)

