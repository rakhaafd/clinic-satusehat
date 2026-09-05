import frappe
from frappe.model.document import Document
import json
from clinic_satusehat.satusehat_client import send_resource, get_organization_id


class SatuSehatPayloadGenerator(Document):
	def before_save(self):
		# Preserve manual ID overrides if user edited the JSON before saving
		self.med_ref_id = getattr(self, "med_ref_id", "") or "GANTI_DENGAN_ID_MEDICATION_SEBELUMNYA"
		self.req_ref_id = getattr(self, "req_ref_id", "") or "GANTI_DENGAN_ID_MEDREQ_SEBELUMNYA"
		self.srv_ref_id = getattr(self, "srv_ref_id", "") or "GANTI_DENGAN_ID_SERVICEREQUEST_SEBELUMNYA"
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
				if "basedOn" in old_payload and old_payload["basedOn"]:
					ref_str = old_payload["basedOn"][0]["reference"]
					if ref_str.startswith("ServiceRequest/"):
						self.srv_ref_id = ref_str.replace("ServiceRequest/", "")
			except Exception:
				pass
		self.generate_payload()

	def generate_payload(self):
		from clinic_satusehat.payload_builders import get_builder
		
		# Fetch Patient Encounter if selected to extract base IDs
		encounter_doc = None
		if self.patient_encounter:
			encounter_doc = frappe.get_doc("Patient Encounter", self.patient_encounter)
			
		self.patient_ihs = getattr(self, "patient_ihs", "") or "GANTI_DENGAN_IHS_PASIEN"
		self.practitioner_ihs = getattr(self, "practitioner_ihs", "") or "GANTI_DENGAN_IHS_DOKTER"
		self.location_id = getattr(self, "location_id", "") or "GANTI_DENGAN_ID_LOCATION"
		self.organization_id = get_organization_id() or "GANTI_DENGAN_ID_KLINIK"
		self.enc_ref_id = getattr(self, "enc_ref_id_override", "") or getattr(self, "enc_ref_id", "") or "GANTI_DENGAN_ID_ENCOUNTER"
		
		if encounter_doc:
			if encounter_doc.patient:
				try:
					patient = frappe.get_doc("Patient", encounter_doc.patient)
					self.patient_ihs = patient.get("satusehat_id") or self.patient_ihs
				except Exception:
					pass
				
			if encounter_doc.practitioner:
				try:
					practitioner = frappe.get_doc("Healthcare Practitioner", encounter_doc.practitioner)
					self.practitioner_ihs = practitioner.get("satusehat_id") or self.practitioner_ihs
				except Exception:
					pass
				
			if encounter_doc.medical_department:
				try:
					dept = frappe.get_doc("Medical Department", encounter_doc.medical_department)
					self.location_id = dept.get("satusehat_id") or dept.get("custom_ihs_location_id") or self.location_id
				except Exception:
					pass

		builder = get_builder(self.resource_type)
		if builder:
			payload = builder.build(self)
		else:
			payload = {
				"resourceType": self.resource_type,
				"status": "not_implemented",
				"message": f"Payload builder for {self.resource_type} is not yet implemented in modular architecture."
			}
			
		self.generated_payload = json.dumps(payload, indent=4)

@frappe.whitelist()
def send_to_satusehat(docname):
	doc = frappe.get_doc("SatuSehat Payload Generator", docname)
	return send_resource(doc, payload_field="generated_payload")

