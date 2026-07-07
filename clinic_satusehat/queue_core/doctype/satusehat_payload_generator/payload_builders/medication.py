import frappe
from .base_builder import PayloadBuilder

class MedicationBuilder(PayloadBuilder):
    def build(self, doc):
        encounter_doc = None
        if doc.patient_encounter:
            encounter_doc = frappe.get_doc("Patient Encounter", doc.patient_encounter)
            
        med_code = "93001019" # Default Paracetamol
        med_display = "Paracetamol"
        
        if encounter_doc and encounter_doc.drug_prescription:
            first_drug = encounter_doc.drug_prescription[0]
            if first_drug.drug_code:
                try:
                    item = frappe.get_doc("Item", first_drug.drug_code)
                    med_code = item.get("kfa_code") or med_code
                    med_display = item.get("item_name") or med_display
                except:
                    pass

        return {
            "resourceType": "Medication",
            "meta": {
                "profile": ["https://fhir.kemkes.go.id/r4/StructureDefinition/Medication"]
            },
            "identifier": [{"system": f"http://sys-ids.kemkes.go.id/medication/{doc.organization_id}", "use": "official", "value": "MED-001"}],
            "code": {"coding": [{"system": "http://sys-ids.kemkes.go.id/kfa", "code": med_code, "display": med_display}]},
            "status": "active",
            "form": {
                "coding": [{"system": "http://terminology.kemkes.go.id/CodeSystem/medication-form", "code": "BS020", "display": "Tablet"}]
            },
            "extension": [
                {
                    "url": "https://fhir.kemkes.go.id/r4/StructureDefinition/MedicationType",
                    "valueCodeableConcept": {
                        "coding": [{"system": "http://terminology.kemkes.go.id/CodeSystem/medication-type", "code": "NC", "display": "Non-compound"}]
                    }
                }
            ]
        }
