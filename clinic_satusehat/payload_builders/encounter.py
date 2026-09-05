import frappe
from .base_builder import PayloadBuilder
from frappe.utils import now_datetime, get_datetime
from clinic_satusehat.satusehat_client import get_organization_id

class EncounterBuilder(PayloadBuilder):
	def build(self, doc):
		org_id = getattr(doc, "organization_id", "") or get_organization_id()
		patient_ihs = getattr(doc, "patient_ihs", "")
		practitioner_ihs = getattr(doc, "practitioner_ihs", "")
		location_id = getattr(doc, "location_id", "")
		doc_name = getattr(doc, "name", "ENC-001")
		
		encounter_doc = None
		if getattr(doc, "patient_encounter", None):
			try:
				encounter_doc = frappe.get_doc("Patient Encounter", doc.patient_encounter)
			except Exception:
				pass
				
		start_time = None
		if getattr(doc, "start_time", None):
			dt = get_datetime(doc.start_time)
			start_time = dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")
		elif encounter_doc and encounter_doc.encounter_date and encounter_doc.encounter_time:
			time_str = str(encounter_doc.encounter_time).zfill(8)
			start_time = f"{encounter_doc.encounter_date}T{time_str}+07:00"
		else:
			start_time = now_datetime().strftime("%Y-%m-%dT%H:%M:%S+00:00")

		return {
			"resourceType": "Encounter",
			"identifier": [
				{
					"system": f"http://sys-ids.kemkes.go.id/encounter/{org_id}",
					"value": getattr(doc, "patient_encounter", "") or doc_name
				}
			],
			"status": getattr(doc, "encounter_status", "arrived") or "arrived",
			"statusHistory": [
				{"status": getattr(doc, "encounter_status", "arrived") or "arrived", "period": {"start": start_time}}
			],
			"class": {
				"system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
				"code": "AMB",
				"display": "ambulatory"
			},
			"subject": {"reference": f"Patient/{patient_ihs}", "display": getattr(doc, "patient_name", "Pasien")},
			"participant": [
				{
					"type": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v3-ParticipationType", "code": "ATND"}]}],
					"individual": {"reference": f"Practitioner/{practitioner_ihs}"}
				}
			],
			"period": {"start": start_time},
			"location": [{"location": {"reference": f"Location/{location_id}"}}],
			"serviceProvider": {"reference": f"Organization/{org_id}"}
		}
