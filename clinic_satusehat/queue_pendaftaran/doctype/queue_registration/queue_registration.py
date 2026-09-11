# Copyright (c) 2026, Rakha and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class QueueRegistration(Document):
	def validate(self):
		if self.reference_patient_registration and (not self.patient or not self.patient_name):
			rp = frappe.db.get_value(
				"Patient Registration",
				self.reference_patient_registration,
				["patient", "patient_name"],
				as_dict=True
			)
			if rp:
				self.patient = rp.get("patient")
				self.patient_name = rp.get("patient_name")
