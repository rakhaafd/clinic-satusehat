import frappe
from frappe.model.document import Document
from frappe.utils import get_datetime
import json
from clinic_satusehat.satusehat_client import send_resource, get_organization_id
from clinic_satusehat.payload_builders import get_builder

class EncounterSatuSehat(Document):
	def before_save(self):
		self.set_start_time()
		self.generate_payload()
		
	def after_insert(self):
		# Create Encounter Validator
		validator_name = self.name.replace("ENC-SS-", "VAL-ENC-")
		doc = frappe.get_doc({
			"doctype": "Encounter Validator",
			"name": validator_name,
			"encounter_satusehat": self.name
		})
		doc.insert(ignore_permissions=True, set_name=validator_name)
		
	def set_start_time(self):
		if self.patient_encounter:
			enc = frappe.get_doc("Patient Encounter", self.patient_encounter)
			if enc.encounter_date and enc.encounter_time:
				dt_str = f"{enc.encounter_date} {enc.encounter_time}"
				self.start_time = get_datetime(dt_str)
	
	def generate_payload(self):
		if not self.start_time:
			frappe.throw("Start Time is required. Ensure Patient Encounter has Date and Time.")
		
		if not getattr(self, "organization_id", None):
			self.organization_id = get_organization_id()

		builder = get_builder("Encounter")
		if not builder:
			frappe.throw("Payload Builder untuk Encounter tidak ditemukan.")

		payload = builder.build(self)
		self.payload_json = json.dumps(payload, indent=4)

@frappe.whitelist()
def send_to_satusehat(docname):
	doc = frappe.get_doc("Encounter SatuSehat", docname)
	return send_resource(doc, payload_field="payload_json")

