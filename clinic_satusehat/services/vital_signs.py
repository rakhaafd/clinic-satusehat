# Copyright (c) 2026, Rakha and contributors
# For license information, please see license.txt

import frappe


def on_vital_signs_save(doc, method=None):
	"""
	Auto-populates patient and company from Queue Registration,
	and updates status_nurse on Queue Registration based on docstatus.
	"""
	queue_reg_name = getattr(doc, "queue_registration", None) or doc.get("queue_registration")
	if not queue_reg_name:
		return

	# Fetch patient and patient_name if missing
	if not doc.get("patient"):
		qr_data = frappe.db.get_value(
			"Queue Registration",
			queue_reg_name,
			["patient", "patient_name", "reference_encounter", "reference_patient_registration"],
			as_dict=True
		)
		patient_id = qr_data.get("patient") if qr_data else None
		patient_name = qr_data.get("patient_name") if qr_data else None

		if not patient_id and qr_data and qr_data.get("reference_encounter"):
			enc_data = frappe.db.get_value(
				"Patient Encounter",
				qr_data.get("reference_encounter"),
				["patient", "patient_name", "company"],
				as_dict=True
			)
			if enc_data:
				patient_id = enc_data.get("patient")
				patient_name = enc_data.get("patient_name")
				if not doc.get("company") and enc_data.get("company"):
					doc.company = enc_data.get("company")

		if not patient_id and qr_data and qr_data.get("reference_patient_registration"):
			pr_data = frappe.db.get_value(
				"Patient Registration",
				qr_data.get("reference_patient_registration"),
				["patient", "patient_name", "company"],
				as_dict=True
			)
			if pr_data:
				patient_id = pr_data.get("patient")
				patient_name = pr_data.get("patient_name")
				if not doc.get("company") and pr_data.get("company"):
					doc.company = pr_data.get("company")

		if patient_id:
			doc.patient = patient_id
		if patient_name:
			doc.patient_name = patient_name

	# Fetch company if missing
	if not doc.get("company"):
		default_company = frappe.db.get_single_value("Healthcare Settings", "default_company") or frappe.db.get_value("Company", {}, "name")
		if default_company:
			doc.company = default_company

	# status_nurse: "Completed" if submitted (docstatus == 1), else "Called"
	new_status = "Completed" if doc.docstatus == 1 else "Called"

	if frappe.db.exists("Queue Registration", queue_reg_name):
		frappe.db.set_value("Queue Registration", queue_reg_name, "status_nurse", new_status)
