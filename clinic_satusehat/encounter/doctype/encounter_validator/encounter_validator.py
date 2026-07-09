# Copyright (c) 2026, rakha and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class EncounterValidator(Document):
	def autoname(self):
		if self.encounter_satusehat:
			self.name = self.encounter_satusehat.replace("ENC-SS-", "VAL-ENC-")

	def before_save(self):
		if not self.is_new() and self.has_value_changed("status"):
			old_doc = self.get_doc_before_save()
			if old_doc and old_doc.status == "Valid":
				frappe.throw("Tidak dapat mengubah status yang sudah Valid!")

	def on_update(self):
		if self.encounter_satusehat:
			if frappe.db.exists("Encounter SatuSehat", self.encounter_satusehat):
				if self.status == "Rejected":
					frappe.delete_doc("Encounter SatuSehat", self.encounter_satusehat, ignore_permissions=True)
					frappe.msgprint(f"Encounter SatuSehat {self.encounter_satusehat} telah dihapus karena status Validator ditolak.")
				else:
					frappe.db.set_value("Encounter SatuSehat", self.encounter_satusehat, "status", self.status)
					frappe.db.commit()
