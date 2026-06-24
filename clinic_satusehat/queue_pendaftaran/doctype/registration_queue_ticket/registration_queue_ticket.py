import frappe
from frappe.model.document import Document
from frappe.utils import today

class RegistrationQueueTicket(Document):
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
				"Registration Queue Ticket",
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
		# Auto create Clinic Queue Ticket when Registration is done
		if self.status == "Selesai" and getattr(self, "destination_clinic", None) and getattr(self, "patient", None):
			# Prevent duplicate generation on multiple saves
			exists = frappe.db.exists("Clinic Queue Ticket", {
				"patient_name": self.patient,
				"clinic_room": self.destination_clinic,
				"status": ["in", ["Menunggu", "Dipanggil", "Diperiksa"]],
				"creation": [">=", today()]
			})
			
			if not exists:
				try:
					ticket = frappe.new_doc("Clinic Queue Ticket")
					ticket.source_registration_ticket = self.name
					ticket.patient_name = self.patient
					ticket.clinic_room = self.destination_clinic
					ticket.insert(ignore_permissions=True)
					frappe.msgprint(f"Tiket Antrean Poli berhasil dibuat otomatis (Tujuan: {self.destination_clinic}).")
				except Exception as e:
					frappe.log_error(message=str(e), title="Auto Create Clinic Queue Failed")

			# Automatically call the next patient in the queue
			next_ticket = frappe.get_all(
				"Registration Queue Ticket",
				filters={"status": "Menunggu", "creation": [">=", today()]},
				order_by="creation asc",
				limit=1
			)
			if next_ticket:
				# Use db_set to avoid triggering unnecessary full saves or recursion
				frappe.db.set_value("Registration Queue Ticket", next_ticket[0].name, "status", "Dipanggil")
