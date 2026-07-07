import frappe
from frappe.model.document import Document
import json
import requests


def _satusehat_headers():
    import requests
    import frappe
    client_id = frappe.conf.get("satusehat_client_id")
    client_secret = frappe.conf.get("satusehat_client_secret")
    auth_url = frappe.conf.get("satusehat_auth_url") or "https://api-satusehat-stg.dto.kemkes.go.id/oauth2/v1"
    
    token_url = f"{auth_url}/accesstoken?grant_type=client_credentials"
    data = {"client_id": client_id, "client_secret": client_secret}
    
    res = requests.post(token_url, data=data, timeout=10)
    if res.status_code == 200:
        token = res.json().get("access_token")
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    frappe.throw(f"Failed to get SatuSehat Token: {res.text}")


class SatuSehatPayloadGenerator(Document):
	def before_save(self):
		import json
		
		# Preserve manual ID overrides if user edited the JSON before saving
		self.med_ref_id = "GANTI_DENGAN_ID_MEDICATION_SEBELUMNYA"
		self.req_ref_id = "GANTI_DENGAN_ID_MEDREQ_SEBELUMNYA"
		if self.generated_payload:
			try:
				old_payload = json.loads(self.generated_payload)
				if "medicationReference" in old_payload:
					ref_str = old_payload["medicationReference"]["reference"]
					if ref_str.startswith("Medication/"):
						self.med_ref_id = ref_str.replace("Medication/", "")
				if "authorizingPrescription" in old_payload and old_payload["authorizingPrescription"]:
					ref_str = old_payload["authorizingPrescription"][0]["reference"]
					if ref_str.startswith("MedicationRequest/"):
						self.req_ref_id = ref_str.replace("MedicationRequest/", "")
			except:
				pass
		self.generate_payload()

	def generate_payload(self):
		from .payload_builders import get_builder
		
		# Fetch Patient Encounter if selected to extract base IDs
		encounter_doc = None
		if self.patient_encounter:
			encounter_doc = frappe.get_doc("Patient Encounter", self.patient_encounter)
			
		self.patient_ihs = "GANTI_DENGAN_IHS_PASIEN"
		self.practitioner_ihs = "GANTI_DENGAN_IHS_DOKTER"
		self.location_id = "GANTI_DENGAN_ID_LOKASI_RUANGAN"
		self.organization_id = frappe.conf.get("satusehat_organization_id") or "GANTI_DENGAN_ID_KLINIK"
		self.enc_ref_id = "GANTI_DENGAN_ID_ENCOUNTER_SEBELUMNYA"
		
		if encounter_doc:
			self.enc_ref_id = getattr(self, "enc_ref_id_override", "") or self.enc_ref_id
			if encounter_doc.patient:
				try:
					patient = frappe.get_doc("Patient", encounter_doc.patient)
					self.patient_ihs = patient.custom_ihs_number or self.patient_ihs
				except: pass
				
			if encounter_doc.practitioner:
				try:
					practitioner = frappe.get_doc("Healthcare Practitioner", encounter_doc.practitioner)
					self.practitioner_ihs = practitioner.custom_ihs_number or self.practitioner_ihs
				except: pass
				
			if encounter_doc.medical_department:
				try:
					dept = frappe.get_doc("Medical Department", encounter_doc.medical_department)
					self.location_id = dept.custom_ihs_location_id or self.location_id
				except: pass

		builder = get_builder(self.resource_type)
		if builder:
			payload = builder.build(self)
		else:
			payload = {
				"resourceType": self.resource_type,
				"status": "not_implemented",
				"message": f"Payload builder for {self.resource_type} is not yet implemented in modular architecture."
			}
			
		import json
		self.generated_payload = json.dumps(payload, indent=4)

@frappe.whitelist()
def send_to_satusehat(docname):
	doc = frappe.get_doc("SatuSehat Payload Generator", docname)
	if not doc.generated_payload:
		frappe.throw("Silakan Save dokumen terlebih dahulu untuk membuat payload!")
		
	payload_json = json.loads(doc.generated_payload)
	resource_type = payload_json.get("resourceType")
	
	# Get the base URL from env
	base_url = frappe.conf.get("satusehat_base_url") or "https://api-satusehat-stg.dto.kemkes.go.id/fhir-r4/v1"
	endpoint = f"{base_url}/{resource_type}"
	
	headers = _satusehat_headers()
	
	try:
		resp = requests.post(endpoint, json=payload_json, headers=headers, timeout=60)
		result_str = f"STATUS CODE: {resp.status_code}\n\n{resp.text}"
		
		frappe.db.set_value("SatuSehat Payload Generator", doc.name, "api_response", result_str)
		
		satusehat_id = ""
		try:
			if resp.status_code in [200, 201]:
				resp_json = resp.json()
				if "id" in resp_json:
					satusehat_id = resp_json["id"]
		except:
			pass
			
		# Log to SatuSehat API Log
		log_doc = frappe.get_doc({
			"doctype": "SatuSehat API Log",
			"reference_doc": doc.name,
			"resource_type": resource_type,
			"satusehat_id": satusehat_id,
			"status_code": resp.status_code,
			"response_json": resp.text
		})
		log_doc.insert(ignore_permissions=True)
		
		frappe.db.commit()
		
		return {"status": resp.status_code, "message": result_str}
	except Exception as e:
		frappe.db.set_value("SatuSehat Payload Generator", doc.name, "api_response", str(e))
		frappe.db.commit()
		return {"status": 500, "message": str(e)}
