# Copyright (c) 2026, rakha and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class ImagingStudyValidator(Document):
	def autoname(self):
		if self.imagingstudy_satusehat:
			self.name = self.imagingstudy_satusehat.replace("IMG-", "VAL-IMG-")

	def before_save(self):
		if not self.is_new() and self.has_value_changed("status"):
			old_doc = self.get_doc_before_save()
			if old_doc and old_doc.status == "Valid":
				frappe.throw("Tidak dapat mengubah status yang sudah Valid!")

	def on_update(self):
		if self.imagingstudy_satusehat:
			if frappe.db.exists("ImagingStudy SatuSehat", self.imagingstudy_satusehat):
				if self.status == "Rejected":
					frappe.delete_doc("ImagingStudy SatuSehat", self.imagingstudy_satusehat, ignore_permissions=True)
				else:
					frappe.db.set_value("ImagingStudy SatuSehat", self.imagingstudy_satusehat, "status", self.status)
					frappe.db.commit()
