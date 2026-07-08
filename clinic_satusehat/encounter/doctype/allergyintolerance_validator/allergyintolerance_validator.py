# Copyright (c) 2026, rakha and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class AllergyIntoleranceValidator(Document):
	def autoname(self):
		if self.allergyintolerance_satusehat:
			self.name = self.allergyintolerance_satusehat.replace("ALGI-", "VAL-ALGI-")

	def before_save(self):
		if not self.is_new() and self.has_value_changed("status"):
			old_doc = self.get_doc_before_save()
			if old_doc and old_doc.status == "Valid":
				frappe.throw("Tidak dapat mengubah status yang sudah Valid!")

	def on_update(self):
		if self.allergyintolerance_satusehat:
			if frappe.db.exists("AllergyIntolerance SatuSehat", self.allergyintolerance_satusehat):
				if self.status == "Rejected":
					frappe.delete_doc("AllergyIntolerance SatuSehat", self.allergyintolerance_satusehat, ignore_permissions=True)
					frappe.msgprint(f"AllergyIntolerance SatuSehat {self.allergyintolerance_satusehat} telah dihapus karena status Validator ditolak.")
				else:
					frappe.db.set_value("AllergyIntolerance SatuSehat", self.allergyintolerance_satusehat, "status", self.status)
					frappe.db.commit()
