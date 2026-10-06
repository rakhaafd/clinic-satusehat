import frappe

def autoname_hash(doc, method=None):
	"""
	Hook for autoname to generate random hashed ID for standard Frappe doctypes.
	"""
	if getattr(doc, "name", None) and doc.name != "New " + doc.doctype:
		return  # Already has a name

	prefix_map = {
		"Patient": "HLC-PAT",
		"Healthcare Practitioner": "HLC-PRC",
		"Patient Appointment": "HLC-APP",
		"Patient Encounter": "HLC-ENC",
		"Vital Signs": "HLC-VIT",
		"Patient Registration": "HLC-PREG"
	}

	prefix = prefix_map.get(doc.doctype)
	if prefix:
		hash_str = frappe.generate_hash(length=12).upper()
		doc.name = f"{prefix}-{hash_str}"
