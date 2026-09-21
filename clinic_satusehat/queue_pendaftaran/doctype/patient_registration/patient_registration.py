# Copyright (c) 2026, Rakha and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc


class PatientRegistration(Document):
	def validate(self):
		self.ensure_schedule_time_option()
		self.check_doctor_availability()

	def ensure_schedule_time_option(self):
		if self.practitioner_schedule_time:
			df = self.meta.get_field("practitioner_schedule_time")
			if df:
				options = [x.strip() for x in (df.options or "").split("\n") if x.strip()]
				if self.practitioner_schedule_time not in options:
					options.append(self.practitioner_schedule_time)
					df.options = "\n".join(options)

	def check_doctor_availability(self):
		if self.practitioner and self.appointment_date:
			from clinic_satusehat.api.appointment import get_practitioner_available_slots
			res = get_practitioner_available_slots(self.practitioner, self.appointment_date)
			if res.get("practice_days") and not res.get("has_schedule_on_this_day"):
				prac_name = res.get("practitioner_name") or self.practitioner
				day_name = res.get("day_of_week")
				days_str = ", ".join(res.get("practice_days", []))
				frappe.throw(
					f"Dokter {prac_name} tidak memiliki jadwal praktek pada hari {day_name} ({self.appointment_date}). "
					f"Hari praktek tersedia: {days_str}."
				)

	def after_insert(self):
		from clinic_satusehat.services.patient_registration import on_patient_registration_save
		on_patient_registration_save(self)

	def on_update(self):
		from clinic_satusehat.services.patient_registration import on_patient_registration_save
		on_patient_registration_save(self)


@frappe.whitelist()
def make_patient_encounter(source_name, target_doc=None):
	def set_missing_values(source, target):
		target.patient_registration = source.name
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
