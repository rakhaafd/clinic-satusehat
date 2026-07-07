import os
import shutil

base_dir = "/home/sachi/intern/frappe/frappe-bench-v15/apps/clinic_satusehat/clinic_satusehat/queue_core/doctype/satusehat_payload_generator"
builder_dir = os.path.join(base_dir, "payload_builders")

if not os.path.exists(builder_dir):
    os.makedirs(builder_dir)

# 1. base_builder.py
with open(os.path.join(builder_dir, "base_builder.py"), "w") as f:
    f.write("""import frappe

class PayloadBuilder:
    def build(self, doc):
        raise NotImplementedError("Subclasses must implement build()")
""")

# 2. encounter.py
with open(os.path.join(builder_dir, "encounter.py"), "w") as f:
    f.write("""import frappe
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
""")

# 3. condition.py
with open(os.path.join(builder_dir, "condition.py"), "w") as f:
    f.write("""import frappe
from .base_builder import PayloadBuilder

class ConditionBuilder(PayloadBuilder):
    def build(self, doc):
        encounter_doc = None
        if doc.patient_encounter:
            encounter_doc = frappe.get_doc("Patient Encounter", doc.patient_encounter)
            
        icd_code = doc.get("diagnostic_code") or "K04.1"
        diagnosis_display = "Diagnosis"
        
        if encounter_doc and encounter_doc.diagnosis:
            first_diagnosis = encounter_doc.diagnosis[0]
            if first_diagnosis.diagnosis:
                try:
                    diag = frappe.get_doc("Diagnosis", first_diagnosis.diagnosis)
                    icd_code = diag.get("icd10_code") or diag.get("diagnosis_code") or icd_code
                    diagnosis_display = diag.get("diagnosis_name") or diag.get("description") or diagnosis_display
                except:
                    pass

        return {
            "resourceType": "Condition",
            "clinicalStatus": {
                "coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical", "code": "active", "display": "Active"}]
            },
            "category": [
                {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-category", "code": "encounter-diagnosis", "display": "Encounter Diagnosis"}]}
            ],
            "code": {
                "coding": [{"system": "http://hl7.org/fhir/sid/icd-10", "code": icd_code, "display": diagnosis_display}]
            },
            "subject": {"reference": f"Patient/{doc.patient_ihs}", "display": "Pasien"},
            "encounter": {"reference": f"Encounter/{getattr(doc, 'enc_ref_id', 'GANTI_DENGAN_ID_ENCOUNTER_SEBELUMNYA')}"}
        }
""")

# 4. medication.py
with open(os.path.join(builder_dir, "medication.py"), "w") as f:
    f.write("""import frappe
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
""")

# 5. medication_request.py
with open(os.path.join(builder_dir, "medication_request.py"), "w") as f:
    f.write("""import frappe
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
""")

# 6. medication_dispense.py
with open(os.path.join(builder_dir, "medication_dispense.py"), "w") as f:
    f.write("""import frappe
from .base_builder import PayloadBuilder

class MedicationDispenseBuilder(PayloadBuilder):
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
            "resourceType": "MedicationDispense",
            "identifier": [{"system": f"http://sys-ids.kemkes.go.id/prescription/{doc.organization_id}", "use": "official", "value": "DISP-001"}],
            "status": "completed",
            "medicationReference": {"reference": f"Medication/{getattr(doc, 'med_ref_id', 'GANTI_DENGAN_ID_MEDICATION_SEBELUMNYA')}", "display": med_display},
            "subject": {"reference": f"Patient/{doc.patient_ihs}"},
            "context": {"reference": f"Encounter/{getattr(doc, 'enc_ref_id', 'GANTI_DENGAN_ID_ENCOUNTER_SEBELUMNYA')}"},
            "authorizingPrescription": [{"reference": f"MedicationRequest/{getattr(doc, 'req_ref_id', 'GANTI_DENGAN_ID_MEDREQ_SEBELUMNYA')}"}]
        }
""")

# 7. __init__.py (Router)
with open(os.path.join(builder_dir, "__init__.py"), "w") as f:
    f.write("""from .encounter import EncounterBuilder
from .condition import ConditionBuilder
from .medication import MedicationBuilder
from .medication_request import MedicationRequestBuilder
from .medication_dispense import MedicationDispenseBuilder

_BUILDERS = {
    "Encounter": EncounterBuilder,
    "Condition": ConditionBuilder,
    "Medication": MedicationBuilder,
    "MedicationRequest": MedicationRequestBuilder,
    "MedicationDispense": MedicationDispenseBuilder,
}

def get_builder(resource_type):
    builder_class = _BUILDERS.get(resource_type)
    if builder_class:
        return builder_class()
    return None
""")

print("Builder structure created successfully.")
