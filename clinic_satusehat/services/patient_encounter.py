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
	qr_name = frappe.db.get_value("Queue Registration", {"reference_encounter": doc.name})

	if not qr_name:
		qr = frappe.get_doc({
			"doctype": "Queue Registration",
			"reference_encounter": doc.name,
			"patient": doc.patient,
			"patient_name": doc.patient_name,
			"appointment": getattr(doc, "appointment", None),
			"status_nurse": "Waiting",
			"status_doctor": "Waiting"
		})
		qr.insert(ignore_permissions=True)
	else:
		if doc.docstatus == 1:
			new_status = "Completed"
		elif getattr(doc.flags, "in_insert", False) or doc.creation == doc.modified:
			new_status = "Waiting"
		else:
			new_status = "Called"

		frappe.db.set_value("Queue Registration", qr_name, {
			"status_doctor": new_status,
			"patient": doc.patient,
			"patient_name": doc.patient_name,
			"appointment": getattr(doc, "appointment", None)
		})
