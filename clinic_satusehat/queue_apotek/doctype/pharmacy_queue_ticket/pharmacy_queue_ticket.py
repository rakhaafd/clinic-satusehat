import frappe
from frappe.model.document import Document

class PharmacyQueueTicket(Document):
	def before_insert(self):
		if not self.queue_number:
			pass
	
	def after_insert(self):
		if self.name:
			parts = self.name.split("-")
			if len(parts) > 0:
				self.db_set("queue_number", parts[-1])
