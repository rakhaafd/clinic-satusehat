import frappe
from frappe.model.document import Document
import json
from clinic_satusehat.satusehat_client import send_resource
from clinic_satusehat.payload_builders import get_builder

class ProcedureSatuSehat(Document):
	def before_save(self):
		self.set_ihs_ids()
		self.generate_payload()

	def after_insert(self):
		validator_name = self.name.replace("PRO-SS-", "VAL-PRO-")
		doc = frappe.get_doc({
			"doctype": "Procedure Validator",
			"name": validator_name,
			"procedure_satusehat": self.name
		})
		doc.insert(ignore_permissions=True, set_name=validator_name)

	def set_ihs_ids(self):
		if not self.encounter_satusehat:
			return
		enc = frappe.get_doc("Encounter SatuSehat", self.encounter_satusehat)
		self.patient_ihs = enc.patient_ihs
		self.practitioner_ihs = enc.practitioner_ihs
		self.satusehat_encounter_id = enc.satusehat_id

	def generate_payload(self):
		if not self.satusehat_encounter_id:
			frappe.throw("Encounter SatuSehat belum memiliki SatuSehat ID.")
		if not self.clinical_procedure:
			frappe.throw("Mohon pilih dokumen Clinical Procedure.")
		if not self.procedure_code or not self.procedure_display:
			frappe.throw("Mohon isi Procedure Code dan Procedure Display.")

		encounter_doc = frappe.get_doc("Encounter SatuSehat", self.encounter_satusehat)
		patient_ihs = self.patient_ihs or encounter_doc.patient_ihs
		practitioner_ihs = self.practitioner_ihs or encounter_doc.practitioner_ihs

		if not patient_ihs:
			frappe.throw("Data Patient IHS belum lengkap. Harap pastikan Pasien memiliki IHS ID pada Encounter SatuSehat.")
		if not practitioner_ihs:
			frappe.throw("Data Practitioner IHS belum lengkap. Harap pastikan Dokter/Praktisi memiliki IHS ID pada Encounter SatuSehat.")

		builder = get_builder("Procedure")
		if not builder:
			frappe.throw("Payload Builder untuk Procedure tidak ditemukan.")

		payload = builder.build(self)
		self.payload_json = json.dumps(payload, indent=4)

@frappe.whitelist()
def send_to_satusehat(docname):
	doc = frappe.get_doc("Procedure SatuSehat", docname)
	res = send_resource(doc, payload_field="payload_json")
	if res.get("status") in [200, 201]:
		frappe.db.set_value("Procedure SatuSehat", doc.name, "status", "Valid")
		frappe.db.commit()
		return {"status": 201}
	else:
		frappe.db.set_value("Procedure SatuSehat", doc.name, "status", "Rejected")
		frappe.db.commit()
		return {"status": 400}


