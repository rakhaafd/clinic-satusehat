from .encounter import EncounterBuilder
from .condition import ConditionBuilder
from .procedure import ProcedureBuilder
from .medication import MedicationBuilder
from .medication_request import MedicationRequestBuilder
from .medication_dispense import MedicationDispenseBuilder
from .allergy_intolerance import AllergyIntoleranceBuilder
from .imaging_study import ImagingStudyBuilder
from .service_request import ServiceRequestBuilder
from .clinical_impression import ClinicalImpressionBuilder
from .immunization import ImmunizationBuilder
from .questionnaire_response import QuestionnaireResponseBuilder
from .medication_statement import MedicationStatementBuilder
from .care_plan import CarePlanBuilder
from .specimen import SpecimenBuilder
from .diagnostic_report import DiagnosticReportBuilder
from .observation import ObservationBuilder
from .episode_of_care import EpisodeOfCareBuilder

_BUILDERS = {
    "Encounter": EncounterBuilder,
    "Condition": ConditionBuilder,
    "Observation": ObservationBuilder,
    "Procedure": ProcedureBuilder,
    "Medication": MedicationBuilder,
    "MedicationRequest": MedicationRequestBuilder,
    "MedicationDispense": MedicationDispenseBuilder,
    "AllergyIntolerance": AllergyIntoleranceBuilder,
    "ImagingStudy": ImagingStudyBuilder,
    "ServiceRequest": ServiceRequestBuilder,
    "ClinicalImpression": ClinicalImpressionBuilder,
    "Immunization": ImmunizationBuilder,
    "QuestionnaireResponse": QuestionnaireResponseBuilder,
    "MedicationStatement": MedicationStatementBuilder,
    "CarePlan": CarePlanBuilder,
    "Specimen": SpecimenBuilder,
    "DiagnosticReport": DiagnosticReportBuilder,
    "EpisodeOfCare": EpisodeOfCareBuilder,
}

def get_builder(resource_type):
    builder_class = _BUILDERS.get(resource_type)
    if builder_class:
        return builder_class()
    return None
