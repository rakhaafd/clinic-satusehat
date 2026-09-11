# Copyright (c) 2026, Rakha and contributors
# For license information, please see license.txt

import frappe


def on_vital_signs_save(doc, method=None):
	queue_reg_name = getattr(doc, "queue_registration", None)
	if not queue_reg_name:
		return

	# Fetch patient if missing
	if not doc.patient:
		patient_id = frappe.db.get_value("Queue Registration", queue_reg_name, "patient")
		if not patient_id:
			rp_name = frappe.db.get_value("Queue Registration", queue_reg_name, "reference_register_patient")
			if rp_name:
				patient_id = frappe.db.get_value("Register Patient", rp_name, "patient")
		if patient_id:
			doc.patient = patient_id

	# status_nurse: "Completed" if submitted (docstatus == 1), else "Called"
	new_status = "Completed" if doc.docstatus == 1 else "Called"

	if frappe.db.exists("Queue Registration", queue_reg_name):
		frappe.db.set_value("Queue Registration", queue_reg_name, "status_nurse", new_status)
