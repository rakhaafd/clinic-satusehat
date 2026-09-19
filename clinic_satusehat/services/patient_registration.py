# Copyright (c) 2026, Rakha and contributors
# For license information, please see license.txt

import frappe


def on_patient_registration_save(doc, method=None):
	"""
	Automatically creates Patient Encounter and Queue Registration
	when a Patient Registration is created/inserted.
	"""
	if not doc.name:
		return

	# Check if Patient Encounter already exists for this Patient Registration
	encounter_name = frappe.db.get_value("Patient Encounter", {"patient_registration": doc.name})

	if not encounter_name:
		practitioner = getattr(doc, "practitioner", None) or getattr(doc, "referring_practitioner", None)

		encounter = frappe.get_doc({
			"doctype": "Patient Encounter",
			"patient_registration": doc.name,
			"patient": doc.patient,
			"patient_name": doc.get("patient_name"),
			"patient_sex": doc.get("patient_sex"),
			"patient_age": doc.get("patient_age"),
			"inpatient_record": doc.get("inpatient_record"),
			"company": doc.get("company") or "SatuSehat",
			"medical_department": doc.get("department"),
			"encounter_date": doc.get("appointment_date"),
			"encounter_time": doc.get("appointment_time"),
			"mode_of_payment": doc.get("mode_of_payment"),
			"practitioner": practitioner
		})
		encounter.insert(ignore_permissions=True, ignore_mandatory=True)
