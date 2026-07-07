import frappe
from .base_builder import PayloadBuilder

class EncounterBuilder(PayloadBuilder):
    def build(self, doc):
        encounter_doc = None
        if doc.patient_encounter:
            encounter_doc = frappe.get_doc("Patient Encounter", doc.patient_encounter)
            
        start_time = "2026-07-06T08:00:00+00:00"
        if encounter_doc and encounter_doc.encounter_date and encounter_doc.encounter_time:
            time_str = str(encounter_doc.encounter_time).zfill(8)
            start_time = f"{encounter_doc.encounter_date}T{time_str}+07:00"
        
        return {
            "resourceType": "Encounter",
            "identifier": [
                {
                    "system": f"http://sys-ids.kemkes.go.id/encounter/{doc.organization_id}",
                    "value": encounter_doc.name if encounter_doc else "ANTREAN-001"
                }
            ],
            "status": "arrived",
            "statusHistory": [
                {"status": "arrived", "period": {"start": start_time}}
            ],
            "class": {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": "AMB",
                "display": "ambulatory"
            },
            "subject": {"reference": f"Patient/{doc.patient_ihs}", "display": "Pasien"},
            "participant": [
                {
                    "type": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v3-ParticipationType", "code": "ATND"}]}],
                    "individual": {"reference": f"Practitioner/{doc.practitioner_ihs}"}
                }
            ],
            "period": {"start": start_time},
            "location": [{"location": {"reference": f"Location/{doc.location_id}"}}],
            "serviceProvider": {"reference": f"Organization/{doc.organization_id}"}
        }
