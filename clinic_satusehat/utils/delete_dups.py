import frappe

def delete_duplicates():
	# For Practitioner
	practitioners = frappe.get_all("Healthcare Practitioner", pluck="name")
	for p in practitioners:
		if p.startswith("HLC-PRAC-"):
			print(f"Deleting duplicate Practitioner: {p}")
			frappe.delete_doc("Healthcare Practitioner", p, force=1)

	frappe.db.commit()
	print("Duplicate Practitioners deleted.")
