# Copyright (c) 2026, Rakha and contributors
# For license information, please see license.txt

import frappe


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
			"patient_registration": getattr(doc, "patient_registration", None),
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
			"appointment": getattr(doc, "appointment", None),
			"patient_registration": getattr(doc, "patient_registration", None)
		})
