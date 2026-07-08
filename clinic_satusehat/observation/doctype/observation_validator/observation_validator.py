# Copyright (c) 2026, rakha and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class ObservationValidator(Document):
	def autoname(self):
		if self.observation_satusehat:
			self.name = self.observation_satusehat.replace("OBS-SS-", "VAL-OBS-")

	def before_save(self):
		if not self.is_new() and self.has_value_changed("status"):
			old_doc = self.get_doc_before_save()
			if old_doc and old_doc.status == "Valid":
				frappe.throw("Tidak dapat mengubah status yang sudah Valid!")

	def on_update(self):
		if self.observation_satusehat:
			if frappe.db.exists("Observation SatuSehat", self.observation_satusehat):
				if self.status == "Rejected":
					frappe.delete_doc("Observation SatuSehat", self.observation_satusehat, ignore_permissions=True)
					frappe.msgprint(f"Observation SatuSehat {self.observation_satusehat} telah dihapus karena status Validator ditolak.")
				else:
					frappe.db.set_value("Observation SatuSehat", self.observation_satusehat, "validation_status", self.status)
					frappe.db.commit()
