# Copyright (c) 2026, rakha and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import json
from clinic_satusehat.satusehat_client import send_resource, get_organization_id
from clinic_satusehat.payload_builders import get_builder

class AllergyIntoleranceSatuSehat(Document):
	def after_insert(self):
		if not frappe.db.exists("AllergyIntolerance Validator", {"allergyintolerance_satusehat": self.name}):
			doc_val = frappe.new_doc("AllergyIntolerance Validator")
			doc_val.allergyintolerance_satusehat = self.name
			doc_val.status = self.status
			doc_val.insert(ignore_permissions=True)

@frappe.whitelist()
def send_to_satusehat(docname):
	doc = frappe.get_doc("AllergyIntolerance SatuSehat", docname)
	if doc.status != "Valid":
		frappe.throw("Dokumen harus divalidasi terlebih dahulu (status Valid).")
		
	if doc.satusehat_id:
		frappe.throw("Dokumen ini sudah terkirim ke SatuSehat.")

	builder = get_builder("AllergyIntolerance")
	payload = builder.build(doc)

	doc.db_set("payload_json", json.dumps(payload, indent=2))
	return send_resource(doc, resource_type="AllergyIntolerance", payload_field="payload_json")
