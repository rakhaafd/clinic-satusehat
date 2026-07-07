import frappe
from .base_builder import PayloadBuilder

class MedicationRequestBuilder(PayloadBuilder):
    def build(self, doc):
        encounter_doc = None
        if doc.patient_encounter:
            encounter_doc = frappe.get_doc("Patient Encounter", doc.patient_encounter)
            
        med_display = "Paracetamol"
        if encounter_doc and encounter_doc.drug_prescription:
            first_drug = encounter_doc.drug_prescription[0]
            if first_drug.drug_code:
                try:
                    item = frappe.get_doc("Item", first_drug.drug_code)
                    med_display = item.get("item_name") or med_display
                except:
                    pass

        return {
            "resourceType": "MedicationRequest",
            "identifier": [{"system": f"http://sys-ids.kemkes.go.id/prescription/{doc.organization_id}", "use": "official", "value": "RX-001"}],
            "status": "active",
            "intent": "order",
            "category": [
                {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/medicationrequest-category", "code": "outpatient", "display": "Outpatient"}]}
            ],
            "medicationReference": {"reference": f"Medication/{getattr(doc, 'med_ref_id', 'GANTI_DENGAN_ID_MEDICATION_SEBELUMNYA')}", "display": med_display},
            "subject": {"reference": f"Patient/{doc.patient_ihs}"},
            "encounter": {"reference": f"Encounter/{getattr(doc, 'enc_ref_id', 'GANTI_DENGAN_ID_ENCOUNTER_SEBELUMNYA')}"},
            "authoredOn": "2026-07-06T09:00:00+07:00",
            "requester": {"reference": f"Practitioner/{doc.practitioner_ihs}"},
            "dosageInstruction": [
                {
                    "text": "3x Sehari 1 Tablet",
                    "timing": {
                        "repeat": {"frequency": 3, "period": 1, "periodUnit": "d"}
                    }
                }
            ]
        }
