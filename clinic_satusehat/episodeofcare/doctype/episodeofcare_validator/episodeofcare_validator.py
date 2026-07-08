# Copyright (c) 2026, rakha and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class EpisodeOfCareValidator(Document):
	def autoname(self):
		if self.episodeofcare_satusehat:
			self.name = self.episodeofcare_satusehat.replace("EOC-", "VAL-EOC-")

	def before_save(self):
		if not self.is_new() and self.has_value_changed("status"):
			old_doc = self.get_doc_before_save()
			if old_doc and old_doc.status == "Valid":
				frappe.throw("Tidak dapat mengubah status yang sudah Valid!")

	def on_update(self):
		if self.episodeofcare_satusehat:
			if frappe.db.exists("EpisodeOfCare SatuSehat", self.episodeofcare_satusehat):
				if self.status == "Rejected":
					frappe.delete_doc("EpisodeOfCare SatuSehat", self.episodeofcare_satusehat, ignore_permissions=True)
				else:
					frappe.db.set_value("EpisodeOfCare SatuSehat", self.episodeofcare_satusehat, "status", self.status)
					frappe.db.commit()
