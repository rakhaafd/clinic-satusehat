import frappe
from frappe.model.document import Document
import json
from clinic_satusehat.satusehat_client import send_resource
from clinic_satusehat.payload_builders import get_builder

class ConditionSatuSehat(Document):
	def before_save(self):
		self.set_icd_code()
		self.generate_payload()
		
	def after_insert(self):
		validator_name = self.name.replace("CND-SS-", "VAL-CND-")
		doc = frappe.get_doc({
			"doctype": "Condition Validator",
			"name": validator_name,
			"condition_satusehat": self.name
		})
		doc.insert(ignore_permissions=True, set_name=validator_name)

	def set_icd_code(self):
		if not self.icd_code and self.patient_encounter:
			encounter_doc = frappe.get_doc("Patient Encounter", self.patient_encounter)
			if encounter_doc.diagnosis:
				first_diagnosis = encounter_doc.diagnosis[0]
				if first_diagnosis.diagnosis:
					try:
						diag = frappe.get_doc("Diagnosis", first_diagnosis.diagnosis)
						self.icd_code = diag.get("icd10_code") or diag.get("diagnosis_code")
						self.diagnosis_display = diag.get("diagnosis_name") or diag.get("description")
					except Exception:
						pass

		if not self.icd_code:
			frappe.throw("Mohon isi ICD-10 Code untuk Diagnosis ini.")

		if not self.diagnosis_display:
			self.diagnosis_display = "Diagnosis"

	def generate_payload(self):
		if not self.satusehat_encounter_id:
			frappe.throw("Encounter SatuSehat belum memiliki SatuSehat ID. Pastikan Encounter sudah sukses dikirim.")
			
		builder = get_builder("Condition")
		if not builder:
			frappe.throw("Payload Builder untuk Condition tidak ditemukan.")
			
		payload = builder.build(self)
		self.payload_json = json.dumps(payload, indent=4)

@frappe.whitelist()
def send_to_satusehat(docname):
	doc = frappe.get_doc("Condition SatuSehat", docname)
	return send_resource(doc, payload_field="payload_json")

