import frappe

def set_patient_naming_series():
	"""
	Set Healthcare Settings patient_name_by to Naming Series (HLC-PAT-.YYYY.-.#####)
	"""
	if frappe.db.exists("DocType", "Healthcare Settings"):
		frappe.db.set_single_value("Healthcare Settings", "patient_name_by", "Naming Series")
		frappe.db.commit