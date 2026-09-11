# Copyright (c) 2026, Rakha and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class QueueRegistration(Document):
	def validate(self):
		if self.reference_encounter:
			enc = frappe.db.get_value(
				"Patient Encounter",
				self.reference_encounter,
				["patient", "patient_name", "appointment", "patient_registration"],
				as_dict=True
			)
			if enc:
				if not self.patient:
					self.patient = enc.get("patient")
				if not self.patient_name:
					self.patient_name = enc.get("patient_name")
				if not self.appointment:
					self.appointment = enc.get("appointment")
				if not self.patient_registration:
					self.patient_registration = enc.get("patient_registration")
