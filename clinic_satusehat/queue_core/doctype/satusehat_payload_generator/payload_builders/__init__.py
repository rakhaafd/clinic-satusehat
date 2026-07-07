from .encounter import EncounterBuilder
from .condition import ConditionBuilder
from .medication import MedicationBuilder
from .medication_request import MedicationRequestBuilder
from .medication_dispense import MedicationDispenseBuilder
from .allergy_intolerance import AllergyIntoleranceBuilder
from .imaging_study import ImagingStudyBuilder
from .service_request import ServiceRequestBuilder
from .clinical_impression import ClinicalImpressionBuilder

_BUILDERS = {
    "Encounter": EncounterBuilder,
    "Condition": ConditionBuilder,
    "Medication": MedicationBuilder,
    "MedicationRequest": MedicationRequestBuilder,
    "MedicationDispense": MedicationDispenseBuilder,
    "AllergyIntolerance": AllergyIntoleranceBuilder,
    "ImagingStudy": ImagingStudyBuilder,
    "ServiceRequest": ServiceRequestBuilder,
    "ClinicalImpression": ClinicalImpressionBuilder,
}

def get_builder(resource_type):
    builder_class = _BUILDERS.get(resource_type)
    if builder_class:
        return builder_class()
    return None
