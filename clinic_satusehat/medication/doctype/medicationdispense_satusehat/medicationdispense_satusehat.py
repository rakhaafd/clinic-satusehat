import frappe
from frappe.model.document import Document
import json
from clinic_satusehat.satusehat_client import send_resource, get_organization_id
from clinic_satusehat.payload_builders import get_builder

class MedicationDispenseSatuSehat(Document):
	def after_insert(self):
		if not frappe.db.exists("MedicationDispense Validator", {"medication_dispense_satusehat": self.name}):
			doc_val = frappe.new_doc("MedicationDispense Validator")
			doc_val.medication_dispense_satusehat = self.name
			doc_val.status = self.status
			doc_val.insert(ignore_permissions=True)

	@frappe.whitelist()
	def fetch_drugs_from_request(self):
		if not self.medication_request_satusehat:
			frappe.throw("Pilih MedicationRequest SatuSehat terlebih dahulu.")
		
		req_doc = frappe.get_doc("MedicationRequest SatuSehat", self.medication_request_satusehat)
		
		self.set("items", [])
		count = 0
		for req_item in req_doc.items:
			med_id = getattr(req_item, "medication_id", None)
			if not med_id and req_item.item_code:
				med_id = frappe.db.get_value("Item", req_item.item_code, "satusehat_id")

			req_id = getattr(req_item, "medication_request_id", None)
			if req_id:
				self.append("items", {
					"item_code": req_item.item_code,
					"item_name": req_item.item_name,
					"kfa_code": req_item.kfa_code,
					"kfa_display": req_item.kfa_display,
					"dosage": req_item.dosage,
					"medication_id": med_id,
					"medication_request_id": req_id,
					"validation_status": "Waiting"
				})
				count += 1
		
		if count == 0:
			frappe.msgprint(
				"<b>Tidak ditemukan obat yang berstatus Valid (memiliki ID Resep SATUSEHAT).</b><br><br>"
				"<b>Penyebab & Solusi:</b><br>"
				"1. Memiliki ID Obat saja (pada Item Master) belum cukup untuk Penyerahan Obat (MedicationDispense).<br>"
				"2. Penyerahan Obat memerlukan <b>MedicationRequest ID</b> (ID Resep resmi dari Kemenkes).<br>"
				"3. Pastikan Anda sudah membuka dokumen <b>MedicationRequest SatuSehat</b> tersebut dan menekan tombol <b>Send to SatuSehat</b> sampai resep sukses terkirim."
			)
		else:
			frappe.msgprint(f"Berhasil menarik {count} obat.")

@frappe.whitelist()
def send_to_satusehat(docname):
	doc = frappe.get_doc("MedicationDispense SatuSehat", docname)
	if doc.status != "Valid":
		frappe.throw("Dokumen harus divalidasi terlebih dahulu (status Valid).")
	
	if not doc.items:
		frappe.throw("Tidak ada obat yang akan dikirim. Silakan Fetch terlebih dahulu.")

	org_id = get_organization_id()
	builder = get_builder("MedicationDispense")

	total_valid = 0
	total_rejected = 0

	for item in doc.items:
		if item.validation_status == "Valid" and item.medication_dispense_id:
			total_valid += 1
			continue
			
		if not item.medication_request_id:
			item.validation_status = "Rejected"
			item.api_response = "MedicationRequest ID kosong."
			total_rejected += 1
			continue

		class DummyItemDoc:
			organization_id = org_id
			patient_ihs = doc.patient_ihs
			satusehat_encounter_id = doc.satusehat_encounter_id
			medication_id = item.medication_id
			medication_request_id = item.medication_request_id
			name = f"{docname}-{item.item_code}"
			kfa_display = item.kfa_display

		dispense_payload = builder.build(DummyItemDoc())

		class TempItemDoc:
			doctype = "MedicationDispense SatuSehat"
			name = doc.name
			payload_json = json.dumps(dispense_payload)

		res = send_resource(TempItemDoc(), resource_type="MedicationDispense")
		item.api_response = res.get("message")
		
		if res.get("status") in [200, 201]:
			dispense_id = res.get("satusehat_id") or (res.get("satusehat_ids")[0] if res.get("satusehat_ids") else None)
			item.medication_dispense_id = dispense_id
			item.validation_status = "Valid"
			total_valid += 1
		else:
			item.validation_status = "Rejected"
			total_rejected += 1

	doc.save(ignore_permissions=True)
	
	aggregated_responses = {}
	for item in doc.items:
		if item.api_response:
			try:
				aggregated_responses[item.item_code] = json.loads(item.api_response)
			except Exception:
				aggregated_responses[item.item_code] = item.api_response
	
	frappe.db.set_value("MedicationDispense SatuSehat", docname, "api_response", json.dumps(aggregated_responses, indent=2))

	if total_rejected == 0 and total_valid > 0:
		frappe.db.set_value("MedicationDispense SatuSehat", docname, "status", "Valid")
		return {"status": 200, "message": "Semua obat berhasil diserahkan ke SatuSehat!"}
	elif total_valid > 0 and total_rejected > 0:
		frappe.db.set_value("MedicationDispense SatuSehat", docname, "status", "Partial")
		return {"status": 206, "message": f"{total_valid} obat berhasil, {total_rejected} gagal."}
	else:
		frappe.db.set_value("MedicationDispense SatuSehat", docname, "status", "Rejected")
		return {"status": 400, "message": "Gagal menyerahkan obat. Periksa API Response."}
