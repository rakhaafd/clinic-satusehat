# Copyright (c) 2026, rakha and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class ConditionValidator(Document):
	def autoname(self):
		if self.condition_satusehat:
			self.name = self.condition_satusehat.replace("CND-SS-", "VAL-CND-")

	def before_save(self):
		if not self.is_new() and self.has_value_changed("status"):
			old_doc = self.get_doc_before_save()
			if old_doc and old_doc.status == "Valid":
				frappe.throw("Tidak dapat mengubah status yang sudah Valid!")

	def on_update(self):
		if self.condition_satusehat:
			if frappe.db.exists("Condition SatuSehat", self.condition_satusehat):
				if self.status == "Rejected":
					frappe.delete_doc("Condition SatuSehat", self.condition_satusehat, ignore_permissions=True)
					frappe.msgprint(f"Condition SatuSehat {self.condition_satusehat} telah dihapus karena status Validator ditolak.")
				else:
					frappe.db.set_value("Condition SatuSehat", self.condition_satusehat, "validation_status", self.status)
					frappe.db.commit()
