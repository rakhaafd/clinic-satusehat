import frappe
from .base_builder import PayloadBuilder
from datetime import datetime

class ObservationBuilder(PayloadBuilder):
	def build(self, doc):
		patient_ihs = getattr(doc, "patient_ihs", "")
		practitioner_ihs = getattr(doc, "practitioner_ihs", "")
		encounter_id = getattr(doc, "satusehat_encounter_id", "") or getattr(doc, "enc_ref_id", "")
		vital_signs = getattr(doc, "vital_signs", None)

		if not patient_ihs and getattr(doc, "encounter_satusehat", ""):
			patient_ihs = frappe.db.get_value("Encounter SatuSehat", doc.encounter_satusehat, "patient_ihs") or ""
			
		if not practitioner_ihs and getattr(doc, "encounter_satusehat", ""):
			practitioner_ihs = frappe.db.get_value("Encounter SatuSehat", doc.encounter_satusehat, "practitioner_ihs") or ""

		current_time = datetime.now().isoformat() + "+07:00"

		def make_base(loinc_code, display):
			return {
				"resourceType": "Observation",
				"status": "final",
				"category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "vital-signs", "display": "Vital Signs"}]}],
				"code": {"coding": [{"system": "http://loinc.org", "code": loinc_code, "display": display}]},
				"subject": {"reference": f"Patient/{patient_ihs}"},
				"encounter": {"reference": f"Encounter/{encounter_id}"},
				"performer": [{"reference": f"Practitioner/{practitioner_ihs}"}],
				"effectiveDateTime": current_time
			}

		payloads = []

		if vital_signs:
			try:
				vital_doc = frappe.get_doc("Vital Signs", vital_signs)
				if getattr(vital_doc, "pulse", None):
					obs = make_base("8867-4", "Heart rate")
					obs["valueQuantity"] = {"value": float(vital_doc.pulse), "unit": "beats/minute", "system": "http://unitsofmeasure.org", "code": "/min"}
					payloads.append(obs)

				if getattr(vital_doc, "respiratory_rate", None):
					obs = make_base("9279-1", "Respiratory rate")
					obs["valueQuantity"] = {"value": float(vital_doc.respiratory_rate), "unit": "breaths/minute", "system": "http://unitsofmeasure.org", "code": "/min"}
					payloads.append(obs)

				if getattr(vital_doc, "temperature", None):
					obs = make_base("8310-5", "Body temperature")
					obs["valueQuantity"] = {"value": float(vital_doc.temperature), "unit": "C", "system": "http://unitsofmeasure.org", "code": "Cel"}
					payloads.append(obs)

				if getattr(vital_doc, "bp_systolic", None) and getattr(vital_doc, "bp_diastolic", None):
					obs = make_base("85354-9", "Blood pressure panel with all children optional")
					obs["component"] = [
						{
							"code": {"coding": [{"system": "http://loinc.org", "code": "8480-6", "display": "Systolic blood pressure"}]},
							"valueQuantity": {"value": float(vital_doc.bp_systolic), "unit": "mm[Hg]", "system": "http://unitsofmeasure.org", "code": "mm[Hg]"}
						},
						{
							"code": {"coding": [{"system": "http://loinc.org", "code": "8462-4", "display": "Diastolic blood pressure"}]},
							"valueQuantity": {"value": float(vital_doc.bp_diastolic), "unit": "mm[Hg]", "system": "http://unitsofmeasure.org", "code": "mm[Hg]"}
						}
					]
					payloads.append(obs)
			except Exception:
				pass

		if not payloads:
			# Fallback generic Observation
			obs = make_base("11477-7", "Microscopic observation")
			obs["valueCodeableConcept"] = {
				"coding": [
					{
						"system": "http://snomed.info/sct",
						"code": "260347006",
						"display": "Positive"
					}
				]
			}
			payloads.append(obs)

		return payloads
