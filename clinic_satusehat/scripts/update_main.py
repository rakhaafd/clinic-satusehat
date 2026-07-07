import os
import re

file_path = "/home/sachi/intern/frappe/frappe-bench-v15/apps/clinic_satusehat/clinic_satusehat/queue_core/doctype/satusehat_payload_generator/satusehat_payload_generator.py"
with open(file_path, "r") as f:
    content = f.read()

# Define the new generate_payload method
new_method = """	def generate_payload(self):
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
"""

# Replace the entire generate_payload method
# We need to find the start of `def generate_payload(self):` and replace everything until `def send_to_satusehat(docname):`
# Because it's huge, regex with DOTALL is best

pattern = r'\tdef generate_payload\(self\):.*?(?=@frappe\.whitelist\(\)\ndef send_to_satusehat\(docname\):)'
new_content = re.sub(pattern, new_method + '\n', content, flags=re.DOTALL)

with open(file_path, "w") as f:
    f.write(new_content)

print("Main file updated successfully.")
