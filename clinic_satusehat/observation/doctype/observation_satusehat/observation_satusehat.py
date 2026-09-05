import frappe
from frappe.model.document import Document
import json
from clinic_satusehat.satusehat_client import send_resource
from clinic_satusehat.payload_builders import get_builder

class ObservationSatuSehat(Document):
	def before_save(self):
		self.set_ihs_ids()
		self.generate_payload()
		
	def after_insert(self):
		validator_name = self.name.replace("OBS-SS-", "VAL-OBS-")
		doc = frappe.get_doc({
			"doctype": "Observation Validator",
			"name": validator_name,
			"observation_satusehat": self.name
		})
		doc.insert(ignore_permissions=True, set_name=validator_name)

	def set_ihs_ids(self):
		if not self.patient_ihs and self.patient:
			try:
				patient_doc = frappe.get_doc("Patient", self.patient)
				self.patient_ihs = patient_doc.get("satusehat_id") or patient_doc.get("custom_ihs_number") or "GANTI_DENGAN_IHS_PASIEN"
			except Exception:
				pass

		if not self.practitioner_ihs and self.encounter_satusehat:
			try:
				encounter_doc = frappe.get_doc("Encounter SatuSehat", self.encounter_satusehat)
				self.practitioner_ihs = encounter_doc.practitioner_ihs or "GANTI_DENGAN_IHS_DOKTER"
			except Exception:
				pass

	def generate_payload(self):
		if not self.satusehat_encounter_id:
			frappe.throw("Encounter SatuSehat belum memiliki SatuSehat ID.")
		if not self.vital_signs:
			frappe.throw("Mohon pilih dokumen Vital Signs.")

		builder = get_builder("Observation")
		payloads = builder.build(self)

		if not payloads:
			frappe.throw("Dokumen Vital Signs tidak memiliki data Nadi, Pernapasan, Suhu, atau Tekanan Darah yang valid.")
			
		self.payload_json = json.dumps(payloads, indent=4)


@frappe.whitelist()
def send_to_satusehat(docname):
	doc = frappe.get_doc("Observation SatuSehat", docname)
	if not doc.payload_json:
		frappe.throw("Silakan Save dokumen terlebih dahulu untuk membuat payload!")

	return send_resource(doc, resource_type="Observation", payload_field="payload_json")
