import frappe
import json
from clinic_satusehat.satusehat_client import send_resource, get_organization_id
from clinic_satusehat.payload_builders import get_builder

@frappe.whitelist()
def register_item_medication(item_code):
	"""
	Mendaftarkan Item obat di SIMRS (berdasarkan KFA Code) ke SATUSEHAT Kemenkes sebagai Medication FHIR Resource.
	"""
	item = frappe.get_doc("Item", item_code)
	if not item.kfa_code:
		frappe.throw("Mohon isi KFA Code terlebih dahulu di Item ini.")

	if item.satusehat_id:
		return {"status": "success", "satusehat_id": item.satusehat_id, "message": "Item ini sudah memiliki SatuSehat ID."}

	org_id = get_organization_id()
	
	class DummyItemDoc:
		organization_id = org_id
		kfa_code = item.kfa_code
		kfa_display = item.kfa_display or item.item_name
		name = item_code

	builder = get_builder("Medication")
	medication_payload = builder.build(DummyItemDoc())

	class TempItemDoc:
		doctype = "Item"
		name = item.name
		payload_json = json.dumps(medication_payload)

	res = send_resource(TempItemDoc(), resource_type="Medication")
	if res.get("status") in [200, 201]:
		med_id = res.get("satusehat_id")
		if med_id:
			item.db_set("satusehat_id", med_id)
			frappe.db.commit()
		return {"status": "success", "satusehat_id": med_id, "message": "Berhasil didaftarkan ke SatuSehat!"}
	else:
		frappe.throw(f"Gagal mendaftarkan Medication: {res.get('message')}")
