import frappe

def set_patient_naming_series():
	"""
	Set Healthcare Settings patient_name_by to Naming Series (HLC-PAT-.YYYY.-.#####)
	and sync tabSeries counter with max existing Patient ID.
	"""
	if frappe.db.exists("DocType", "Healthcare Settings"):
		frappe.db.set_single_value("Healthcare Settings", "patient_name_by", "Naming Series")

	import datetime
	year = datetime.datetime.now().year
	prefix = f"HLC-PAT-{year}-"
	patients = frappe.db.get_all("Patient", filters={"name": ["like", f"{prefix}%"]}, fields=["name"])
	max_val = 0
	for p in patients:
		try:
			val = int(p.name.split("-")[-1])
			if val > max_val:
				max_val = val
		except Exception:
			pass

	if max_val > 0:
		res = frappe.db.sql("SELECT `current` FROM `tabSeries` WHERE `name` = %s", (prefix,))
		current_series = res[0][0] if res else None
		if current_series is None or current_series < max_val:
			frappe.db.sql("INSERT INTO `tabSeries` (`name`, `current`) VALUES (%s, %s) ON DUPLICATE KEY UPDATE `current` = %s", (prefix, max_val, max_val))

	frappe.db.commit()