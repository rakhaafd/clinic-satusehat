# Copyright (c) 2026, rakha and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class CarePlanValidator(Document):
	def autoname(self):
		if self.careplan_satusehat:
			self.name = self.careplan_satusehat.replace("CPL-", "VAL-CPL-")

	def before_save(self):
		if not self.is_new() and self.has_value_changed("status"):
			old_doc = self.get_doc_before_save()
			if old_doc and old_doc.status == "Valid":
				frappe.throw("Tidak dapat mengubah status yang sudah Valid!")

	def on_update(self):
		if self.careplan_satusehat:
			if frappe.db.exists("CarePlan SatuSehat", self.careplan_satusehat):
				if self.status == "Rejected":
					frappe.delete_doc("CarePlan SatuSehat", self.careplan_satusehat, ignore_permissions=True)
				else:
					frappe.db.set_value("CarePlan SatuSehat", self.careplan_satusehat, "status", self.status)
					frappe.db.commit()
