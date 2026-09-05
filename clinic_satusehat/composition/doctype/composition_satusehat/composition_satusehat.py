import frappe
from frappe.model.document import Document
import json
from datetime import datetime
from clinic_satusehat.satusehat_client import send_resource

class CompositionSatuSehat(Document):
	def before_save(self):
		self.generate_payload()

	def after_insert(self):
		validator_name = self.name.replace("COM-SS-", "VAL-COM-")
		doc = frappe.get_doc({
			"doctype": "Composition Validator",
			"name": validator_name,
			"composition_satusehat": self.name
		})
		doc.insert(ignore_permissions=True, set_name=validator_name)

	def generate_payload(self):
		if not self.encounter_satusehat:
			return
		if not self.satusehat_encounter_id:
			frappe.throw("Encounter SatuSehat belum memiliki SatuSehat ID.")

		from clinic_satusehat.payload_builders import get_builder
		builder = get_builder("Composition")
		payload = builder.build(self)
		self.payload_json = json.dumps(payload, indent=4)

@frappe.whitelist()
def send_to_satusehat(docname):
	doc = frappe.get_doc("Composition SatuSehat", docname)
	res = send_resource(doc, payload_field="payload_json")
	if res.get("status") in [200, 201]:
		frappe.db.set_value("Composition SatuSehat", doc.name, "status", "Valid")
		frappe.db.commit()
		return {"status": 201}
	else:
		frappe.db.set_value("Composition SatuSehat", doc.name, "status", "Rejected")
		frappe.db.commit()
		return {"status": 400}

