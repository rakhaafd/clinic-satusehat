import frappe

def rename_all():
	# For Patient
	patients = frappe.get_all("Patient", pluck="name")
	for p in patients:
		# check if it already has the hash format (len == 20 for HLC-PAT-XXXXXXXXXXXX)
		# "HLC-PAT-" is 8 chars, hash is 12 chars. Total = 20
		if len(p) != 20: 
			hash_str = frappe.generate_hash(length=12).upper()
			new_name = f"HLC-PAT-{hash_str}"
			print(f"Renaming Patient: {p} -> {new_name}")
			frappe.rename_doc("Patient", p, new_name)

	# For Practitioner
	practitioners = frappe.get_all("Healthcare Practitioner", pluck="name")
	for p in practitioners:
		if len(p) != 20:
			hash_str = frappe.generate_hash(length=12).upper()
			new_name = f"HLC-PRC-{hash_str}"
			print(f"Renaming Practitioner: {p} -> {new_name}")
			frappe.rename_doc("Healthcare Practitioner", p, new_name)

	frappe.db.commit()
	print("Selesai! Semua data master lama telah diperbarui.")
