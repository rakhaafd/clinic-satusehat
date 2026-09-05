import frappe
from frappe.model.document import Document
import json
from frappe.utils import get_datetime
from clinic_satusehat.satusehat_client import send_resource, get_organization_id
from clinic_satusehat.payload_builders import get_builder

class EpisodeOfCareSatuSehat(Document):
	def after_insert(self):
		if not frappe.db.exists("EpisodeOfCare Validator", {"episodeofcare_satusehat": self.name}):
			doc_val = frappe.new_doc("EpisodeOfCare Validator")
			doc_val.episodeofcare_satusehat = self.name
			doc_val.status = self.status
			doc_val.insert(ignore_permissions=True)

@frappe.whitelist()
def send_to_satusehat(docname):
	doc = frappe.get_doc("EpisodeOfCare SatuSehat", docname)
	if doc.status != "Valid":
		frappe.throw("Dokumen harus divalidasi terlebih dahulu (status Valid).")
		
	if doc.satusehat_id:
		frappe.throw("Dokumen ini sudah terkirim ke SatuSehat.")

	builder = get_builder("EpisodeOfCare")
	payload = builder.build(doc)
	
	doc.db_set("payload_json", json.dumps(payload, indent=2))
	return send_resource(doc, resource_type="EpisodeOfCare", payload_field="payload_json")

