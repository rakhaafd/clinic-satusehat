import frappe
from frappe.model.document import Document

class ClinicQueueTicket(Document):
	def before_insert(self):
		if not self.queue_number:
			pass
	
	def after_insert(self):
		if self.name:
			parts = self.name.split("-")
			if len(parts) > 0:
				self.db_set("queue_number", parts[-1])

	def on_update(self):
		from frappe.utils import today
		if self.status == "Selesai" and getattr(self, "encounter_ref", None):
			# Check if encounter has drug prescription
			encounter = frappe.get_doc("Patient Encounter", self.encounter_ref)
			if encounter.drug_prescription:
				# Prevent duplicate generation
				exists = frappe.db.exists("Pharmacy Queue Ticket", {
					"source_clinic_ticket": self.name
				})
				
				if not exists:
					try:
						ticket = frappe.new_doc("Pharmacy Queue Ticket")
						ticket.source_clinic_ticket = self.name
						ticket.prescription_ref = self.encounter_ref
						ticket.insert(ignore_permissions=True)
						frappe.msgprint(f"Tiket Antrean Apotek berhasil dibuat otomatis (Resep: {self.encounter_ref}).")
					except Exception as e:
						frappe.log_error(message=str(e), title="Auto Create Pharmacy Queue Failed")
