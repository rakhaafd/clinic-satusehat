import frappe

def sync_patient_nik(doc, method=None):
	"""
	Keep NIK and UID synchronized on Patient doc
	"""
	if getattr(doc, "nik", None) and not getattr(doc, "uid", None):
		doc.uid = doc.nik
	elif getattr(doc, "uid", None) and not getattr(doc, "nik", None):
		doc.nik = doc.uid
