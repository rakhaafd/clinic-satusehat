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

	def validate(self):
		if self.has_value_changed("status") and self.status == "Dipanggil":
			older_ticket = frappe.get_all(
				"Pharmacy Queue Ticket",
				filters={
					"status": "Menunggu",
					"creation": ["<", self.creation],
					"name": ["!=", self.name]
				},
				limit=1
			)
			if older_ticket:
				frappe.throw("Gagal! Tidak bisa memanggil antrean ini karena antrean sebelumnya masih berstatus Menunggu.")

	def on_update(self):
		from frappe.utils import today
		
		# Automatically call the next patient in the queue if current moves to Selesai
		if self.has_value_changed("status") and self.status == "Selesai":
			next_ticket = frappe.get_all(
				"Pharmacy Queue Ticket",
				filters={"status": "Menunggu", "creation": [">=", today()]},
				order_by="creation asc",
				limit=1
			)
			if next_ticket:
				frappe.db.set_value("Pharmacy Queue Ticket", next_ticket[0].name, "status", "Dipanggil")
