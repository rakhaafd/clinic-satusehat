# Copyright (c) 2026, Rakha and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc


class PatientRegistration(Document):
	def after_insert(self):
		self.create_queue_registration()

	def create_queue_registration(self):
		if not frappe.db.exists("Queue Registration", {"reference_patient_registration": self.name}):
			queue_reg = frappe.get_doc({
				"doctype": "Queue Registration",
				"reference_patient_registration": self.name,
				"status_nurse": "Waiting",
				"status_doctor": "Waiting"
			})
			queue_reg.insert(ignore_permissions=True)


@frappe.whitelist()
def make_patient_encounter(source_name, target_doc=None):
	def set_missing_values(source, target):
		target.patient = source.patient
		target.patient_name = source.patient_name
		target.patient_sex = source.patient_sex
		target.patient_age = source.patient_age
		target.inpatient_record = source.inpatient_record
		target.company = source.company
		target.medical_department = source.department
		if getattr(source, "appointment_date", None):
			target.encounter_date = source.appointment_date
		if getattr(source, "appointment_time", None):
			target.encounter_time = source.appointment_time

	doclist = get_mapped_doc(
		"Patient Registration",
		source_name,
		{
			"Patient Registration": {
				"doctype": "Patient Encounter",
				"field_map": {
					"patient": "patient",
					"patient_name": "patient_name",
					"patient_sex": "patient_sex",
					"patient_age": "patient_age",
					"inpatient_record": "inpatient_record",
					"company": "company",
					"department": "medical_department",
					"appointment_date": "encounter_date",
					"appointment_time": "encounter_time"
				}
			}
		},
		target_doc,
		set_missing_values
	)

	return doclist
