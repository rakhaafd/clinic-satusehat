from .encounter import EncounterBuilder
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
