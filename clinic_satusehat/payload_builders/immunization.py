import frappe
from .base_builder import PayloadBuilder
from frappe.utils import now_datetime

class ImmunizationBuilder(PayloadBuilder):
	def build(self, doc):
		patient_ihs = getattr(doc, "patient_ihs", "")
		enc_ref_id = getattr(doc, "enc_ref_id", "") or getattr(doc, "satusehat_encounter_id", "")
		practitioner_ihs = getattr(doc, "practitioner_ihs", "")
		
		vaccine_code = getattr(doc, "vaccine_code", "") or "93001282"
		vaccine_display = getattr(doc, "vaccine_display", "") or "Vaksin COVID-19"
		
		occurrence_dt = getattr(doc, "occurrence_datetime", None)
		if occurrence_dt:
			from frappe.utils import get_datetime
			occurrence_str = get_datetime(occurrence_dt).strftime("%Y-%m-%dT%H:%M:%S+00:00")
		else:
			occurrence_str = now_datetime().strftime("%Y-%m-%dT%H:%M:%S+00:00")
			
		lot_number = getattr(doc, "lot_number", "") or "LOT12345"
		expiration_date = str(getattr(doc, "expiration_date", "") or "2029-01-01")
		dose_number = int(getattr(doc, "dose_number", 1) or 1)

		return {
			"resourceType": "Immunization",
			"status": "completed",
			"vaccineCode": {
				"coding": [
					{
						"system": "http://sys-ids.kemkes.go.id/kfa",
						"code": vaccine_code, 
						"display": vaccine_display
					}
				]
			},
			"patient": {
				"reference": f"Patient/{patient_ihs}"
			},
			"encounter": {
				"reference": f"Encounter/{enc_ref_id}"
			},
			"occurrenceDateTime": occurrence_str,
			"primarySource": True,
			"lotNumber": lot_number,
			"expirationDate": expiration_date,
			"performer": [
				{
					"function": {
						"coding": [
							{
								"system": "http://terminology.hl7.org/CodeSystem/v2-0443",
								"code": "AP",
								"display": "Administering Provider"
							}
						]
					},
					"actor": {
						"reference": f"Practitioner/{practitioner_ihs}"
					}
				}
			],
			"reasonCode": [
				{
					"coding": [
						{
							"system": "http://snomed.info/sct",
							"code": "429060002",
							"display": "Procedure to prevent disease"
						}
					]
				}
			],
			"protocolApplied": [
				{
					"doseNumberPositiveInt": dose_number
				}
			]
		}
