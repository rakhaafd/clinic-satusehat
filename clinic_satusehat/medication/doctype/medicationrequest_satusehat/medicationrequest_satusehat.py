import frappe
from frappe.model.document import Document
import json
from clinic_satusehat.satusehat_client import send_resource, get_organization_id
from clinic_satusehat.payload_builders import get_builder

class MedicationRequestSatuSehat(Document):
	def after_insert(self):
		validator_name = self.name.replace("MED-REQ-", "VAL-MED-")
		doc = frappe.get_doc({
			"doctype": "MedicationRequest Validator",
			"name": validator_name,
			"medication_request_satusehat": self.name
		})
		doc.insert(ignore_permissions=True, set_name=validator_name)

@frappe.whitelist()
def fetch_drugs_from_encounter(docname):
	doc = frappe.get_doc("MedicationRequest SatuSehat", docname)
	if not doc.patient_encounter:
		frappe.throw("Mohon pilih Patient Encounter terlebih dahulu.")
	
	enc = frappe.get_doc("Patient Encounter", doc.patient_encounter)
	doc.set("items", [])
	
	for drug in enc.drugs:
		item_code = drug.medication or drug.drug_code
		if not item_code: continue

		item_doc = frappe.get_doc("Item", item_code)
		kfa_code = item_doc.kfa_code
		kfa_display = item_doc.kfa_display or item_doc.item_name
		
		dosage_instructions = ""
		if drug.dosage:
			dosage_instructions += drug.dosage
		if drug.period:
			dosage_instructions += f" for {drug.period}"

		doc.append("items", {
			"item_code": item_code,
			"item_name": item_doc.item_name,
			"kfa_code": kfa_code,
			"kfa_display": kfa_display,
			"dosage": dosage_instructions
		})
	
	doc.save(ignore_permissions=True)
	return {"status": "success"}

@frappe.whitelist()
def send_to_satusehat(docname):
	doc = frappe.get_doc("MedicationRequest SatuSehat", docname)
	if not doc.items:
		frappe.throw("Tidak ada obat yang akan dikirim.")

	org_id = get_organization_id()
	builder = get_builder("MedicationRequest")

	total_valid = 0
	total_rejected = 0

	for item in doc.items:
		if not item.kfa_code:
			item.validation_status = "Rejected"
			item.api_response = "KFA Code kosong. Silakan lengkapi di Item Master."
			total_rejected += 1
			continue

		med_id = None
		item_doc = frappe.get_doc("Item", item.item_code)
		if item_doc.satusehat_id:
			med_id = item_doc.satusehat_id
			item.medication_id = med_id
		else:
			from clinic_satusehat.api import register_item_medication
			try:
				res = register_item_medication(item.item_code)
				if res and res.get("satusehat_id"):
					med_id = res.get("satusehat_id")
					item.medication_id = med_id
			except Exception as e:
				item.validation_status = "Rejected"
				item.api_response = f"Gagal auto-register Medication: {str(e)}"
				total_rejected += 1
				continue

		if not med_id:
			continue

		class DummyItemDoc:
			organization_id = org_id
			patient_ihs = doc.patient_ihs
			practitioner_ihs = doc.practitioner_ihs
			satusehat_encounter_id = doc.satusehat_encounter_id
			med_ref_id = med_id
			name = f"{docname}-{item.item_code}"
			kfa_display = item.kfa_display
			dosage = item.dosage

		medreq_payload = builder.build(DummyItemDoc())
		item._generated_payload = medreq_payload

		class TempItemDoc:
			doctype = "MedicationRequest SatuSehat"
			name = doc.name
			payload_json = json.dumps(medreq_payload)

		res = send_resource(TempItemDoc(), resource_type="MedicationRequest")
		if res.get("status") in [200, 201]:
			req_id = res.get("satusehat_id") or (res.get("satusehat_ids")[0] if res.get("satusehat_ids") else None)
			item.medication_request_id = req_id
			item.validation_status = "Valid"
			item.api_response = res.get("message")
			total_valid += 1
		else:
			item.validation_status = "Rejected"
			item.api_response = res.get("message")
			total_rejected += 1

	aggregated_responses = {}
	aggregated_payloads = {}
	for item in doc.items:
		if hasattr(item, "_generated_payload"):
			aggregated_payloads[item.item_code] = item._generated_payload
			
		if item.api_response:
			try:
				aggregated_responses[item.item_code] = json.loads(item.api_response)
			except Exception:
				aggregated_responses[item.item_code] = item.api_response
	
	doc.payload_json = json.dumps(aggregated_payloads, indent=2)
	doc.api_response = json.dumps(aggregated_responses, indent=2)

	if total_rejected == 0 and total_valid > 0:
		doc.status = "Valid"
		doc.save(ignore_permissions=True)
		frappe.db.commit()
		return {"status": 200, "message": "Semua resep berhasil dikirim!"}
	elif total_valid > 0 and total_rejected > 0:
		doc.status = "Partial"
		doc.save(ignore_permissions=True)
		frappe.db.commit()
		return {"status": 206, "message": f"{total_valid} resep berhasil, {total_rejected} gagal."}
	else:
		doc.status = "Rejected"
		doc.save(ignore_permissions=True)
		frappe.db.commit()
		return {"status": 400, "message": "Gagal mengirim resep. Periksa API Response."}
