# Copyright (c) 2026, rakha and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class SpecimenValidator(Document):
	def autoname(self):
		if self.specimen_satusehat:
			self.name = self.specimen_satusehat.replace("SPC-", "VAL-SPC-")

	def before_save(self):
		if not self.is_new() and self.has_value_changed("status"):
			old_doc = self.get_doc_before_save()
			if old_doc and old_doc.status == "Valid":
				frappe.throw("Tidak dapat mengubah status yang sudah Valid!")

	def on_update(self):
		if self.specimen_satusehat:
			if frappe.db.exists("Specimen SatuSehat", self.specimen_satusehat):
				if self.status == "Rejected":
					frappe.delete_doc("Specimen SatuSehat", self.specimen_satusehat, ignore_permissions=True)
				else:
					frappe.db.set_value("Specimen SatuSehat", self.specimen_satusehat, "status", self.status)
					frappe.db.commit()
