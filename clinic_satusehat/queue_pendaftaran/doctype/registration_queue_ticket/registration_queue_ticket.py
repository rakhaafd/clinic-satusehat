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
