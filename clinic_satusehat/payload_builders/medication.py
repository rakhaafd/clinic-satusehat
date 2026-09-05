import frappe
from .base_builder import PayloadBuilder
from clinic_satusehat.satusehat_client import get_organization_id

class MedicationBuilder(PayloadBuilder):
	def build(self, doc):
		org_id = getattr(doc, "organization_id", "") or get_organization_id()

		med_code = getattr(doc, "kfa_code", "") or getattr(doc, "med_code", "")
		med_display = getattr(doc, "kfa_display", "") or getattr(doc, "item_name", "") or getattr(doc, "med_display", "")
		doc_name = getattr(doc, "name", "MED-001")

		if not med_code and getattr(doc, "patient_encounter", None):
			try:
				encounter_doc = frappe.get_doc("Patient Encounter", doc.patient_encounter)
				if encounter_doc and getattr(encounter_doc, "drug_prescription", None):
					first_drug = encounter_doc.drug_prescription[0]
					if first_drug.drug_code:
						item = frappe.get_doc("Item", first_drug.drug_code)
						med_code = item.get("kfa_code") or med_code
						med_display = item.get("item_name") or med_display
			except Exception:
				pass

		if not med_code:
			frappe.throw("Mohon isi KFA Code pada Item/Medication terlebih dahulu.")

		form_code = getattr(doc, "form_code", "BS020") or "BS020"
		form_display = getattr(doc, "form_display", "Tablet") or "Tablet"

		return {
			"resourceType": "Medication",
			"meta": {
				"profile": ["https://fhir.kemkes.go.id/r4/StructureDefinition/Medication"]
			},
			"identifier": [{"system": f"http://sys-ids.kemkes.go.id/medication/{org_id}", "use": "official", "value": doc_name}],
			"code": {"coding": [{"system": "http://sys-ids.kemkes.go.id/kfa", "code": med_code, "display": med_display or "Obat"}]},
			"status": "active",
			"form": {
				"coding": [{"system": "http://terminology.kemkes.go.id/CodeSystem/medication-form", "code": form_code, "display": form_display}]
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
