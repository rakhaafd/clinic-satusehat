from datetime import datetime
import frappe

class CompositionBuilder:
    def build(self, doc):
        sections = []
        
        encounter_id = getattr(doc, "satusehat_encounter_id", "") or getattr(doc, "enc_ref_id", "")
        encounter_satusehat_name = getattr(doc, "encounter_satusehat", "")

        if encounter_satusehat_name:
            # 1. Conditions / Diagnosis
            conditions = frappe.get_all("Condition SatuSehat", 
                filters={"encounter_satusehat": encounter_satusehat_name, "validation_status": "Valid"}, 
                fields=["satusehat_id"])
            if conditions:
                entry_list = [{"reference": f"Condition/{c.satusehat_id}"} for c in conditions if c.satusehat_id]
                if entry_list:
                    sections.append({
                        "title": "Diagnosis",
                        "code": {
                            "coding": [{"system": "http://loinc.org", "code": "11450-4", "display": "Problem list - Reported"}]
                        },
                        "entry": entry_list
                    })

            # 2. Observations / Vital Signs
            observations = frappe.get_all("Observation SatuSehat", 
                filters={"encounter_satusehat": encounter_satusehat_name, "validation_status": "Valid"}, 
                fields=["satusehat_ids"])
            obs_entry_list = []
            for obs in observations:
                if obs.satusehat_ids:
                    ids = [i.strip() for i in obs.satusehat_ids.split(",") if i.strip()]
                    for i in ids:
                        obs_entry_list.append({"reference": f"Observation/{i}"})
            if obs_entry_list:
                sections.append({
                    "title": "Vital Signs",
                    "code": {
                        "coding": [{"system": "http://loinc.org", "code": "8716-3", "display": "Vital signs"}]
                    },
                    "entry": obs_entry_list
                })

            # 3. Procedures
            procedures = frappe.get_all("Procedure SatuSehat", 
                filters={"encounter_satusehat": encounter_satusehat_name, "status": "Valid"}, 
                fields=["satusehat_id"])
            if procedures:
                proc_entry_list = [{"reference": f"Procedure/{p.satusehat_id}"} for p in procedures if p.satusehat_id]
                if proc_entry_list:
                    sections.append({
                        "title": "Procedure",
                        "code": {
                            "coding": [{"system": "http://loinc.org", "code": "47519-4", "display": "History of Procedures Document"}]
                        },
                        "entry": proc_entry_list
                    })

        return {
            "resourceType": "Composition",
            "status": "final",
            "type": {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": "18842-5",
                        "display": "Discharge summary"
                    }
                ]
            },
            "subject": {
                "reference": f"Patient/{getattr(doc, 'patient_ihs', '')}"
            },
            "encounter": {
                "reference": f"Encounter/{encounter_id}"
            },
            "date": datetime.now().isoformat() + "+07:00",
            "author": [
                {
                    "reference": f"Practitioner/{getattr(doc, 'practitioner_ihs', '')}"
                }
            ],
            "title": getattr(doc, "composition_title", "") or "Resume Medis",
            "section": sections
        }
