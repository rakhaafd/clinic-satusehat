import frappe
from frappe import _

@frappe.whitelist(allow_guest=True)
def get_hospitals_and_locations():
	"""
	API 1: Mengambil daftar Rumah Sakit (Company), Lokasi, dan Spesialisasi (Medical Department)
	untuk mengisi opsi filter di React Frontend saat pertama kali dimuat.
	"""
	fields = ["name", "company_name", "country"]
	if frappe.db.has_column("Company", "custom_city"):
		fields.append("custom_city")

	hospitals = frappe.db.get_all(
		"Company",
		fields=fields,
		order_by="company_name asc"
	)

	departments_raw = frappe.db.get_all(
		"Medical Department",
		fields=["name"],
		order_by="name asc"
	)
	departments = [{"name": d["name"], "department_name": d["name"]} for d in departments_raw]

	locations = list(set([h.get("custom_city") or h.get("country") for h in hospitals if (h.get("custom_city") or h.get("country"))]))

	return {
		"status": "success",
		"data": {
			"hospitals": hospitals,
			"departments": departments,
			"locations": sorted(locations)
		}
	}


@frappe.whitelist(allow_guest=True)
def get_departments_by_company(company=None):
	"""
	API 2: Mengambil daftar Spesialisasi (Medical Department) yang HANYA ADA
	di Rumah Sakit (Company) tertentu secara dinamis berdasarkan dokter yang praktek.
	"""
	if not company:
		departments_raw = frappe.db.get_all("Medical Department", fields=["name"], order_by="name asc")
		return {"status": "success", "departments": [{"name": d["name"], "department_name": d["name"]} for d in departments_raw]}

	# Search Healthcare Practitioner where hospital matches company, or service unit company matches
	dept_names = set()

	# 1. Check direct hospital match on Healthcare Practitioner
	if frappe.db.has_column("Healthcare Practitioner", "hospital"):
		matched_by_hosp = frappe.db.get_all(
			"Healthcare Practitioner",
			filters={"hospital": company},
			pluck="department"
		)
		dept_names.update([d for d in matched_by_hosp if d])

	# 2. Check Service Units associated with the Company
	service_units = frappe.db.get_all("Healthcare Service Unit", filters={"company": company}, pluck="name")
	if service_units:
		matched_by_su = frappe.db.sql_list("""
			SELECT DISTINCT parent.department
			FROM `tabPractitioner Service Unit Schedule` child
			JOIN `tabHealthcare Practitioner` parent ON child.parent = parent.name
			WHERE child.service_unit IN %s AND parent.department IS NOT NULL
		""", (tuple(service_units),))
		dept_names.update([d for d in matched_by_su if d])

	# Fallback: If no specific practitioner link exists yet, return all departments
	if not dept_names:
		departments_raw = frappe.db.get_all("Medical Department", fields=["name"], order_by="name asc")
		return {"status": "success", "departments": [{"name": d["name"], "department_name": d["name"]} for d in departments_raw]}

	departments_raw = frappe.db.get_all(
		"Medical Department",
		filters={"name": ["in", list(dept_names)]},
		fields=["name"],
		order_by="name asc"
	)
	departments = [{"name": d["name"], "department_name": d["name"]} for d in departments_raw]

	return {
		"status": "success",
		"company": company,
		"departments": departments
	}


@frappe.whitelist(allow_guest=True)
def search_doctors(search_text=None, company=None, department=None, location=None):
	"""
	API 3: Pencarian Dokter utama (Filter berantai: Nama Dokter, Rumah Sakit, Spesialisasi, Lokasi)
	"""
	filters = {}

	if department:
		filters["department"] = department
	if search_text:
		filters["practitioner_name"] = ["like", f"%{search_text}%"]
	if company and frappe.db.has_column("Healthcare Practitioner", "hospital"):
		filters["hospital"] = company

	doctors = frappe.db.get_all(
		"Healthcare Practitioner",
		filters=filters,
		fields=["name", "practitioner_name", "department", "image", "mobile_phone"],
		order_by="practitioner_name asc"
	)

	result = []
	for doc in doctors:
		hosp_name = getattr(doc, "hospital", None) or company or "Klinik Utama"
		result.append({
			"id": doc.name,
			"name": doc.practitioner_name,
			"department": doc.department,
			"department_name": doc.department or "",
			"company": hosp_name,
			"company_name": hosp_name,
			"image": doc.image,
			"mobile": doc.mobile_phone
		})

	return {
		"status": "success",
		"count": len(result),
		"doctors": result
	}
