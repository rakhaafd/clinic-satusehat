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

	def validate(self):
		if self.has_value_changed("status") and self.status == "Dipanggil":
			older_ticket = frappe.get_all(
				"Clinic Queue Ticket",
				filters={
					"status": "Menunggu",
					"creation": ["<", self.creation],
					"name": ["!=", self.name]
				},
				limit=1
			)
			if older_ticket:
				frappe.throw("Gagal! Tidak bisa memanggil antrean ini karena antrean sebelumnya masih berstatus Menunggu.")

		# Validasi backend: Encounter Ref hanya boleh digunakan sekali
		if self.encounter_ref:
			existing_ticket = frappe.db.exists("Clinic Queue Ticket", {
				"encounter_ref": self.encounter_ref,
				"name": ["!=", self.name]
			})
			if existing_ticket:
				frappe.throw(f"Gagal! Patient Encounter '{self.encounter_ref}' sudah digunakan pada tiket '{existing_ticket}'.")

	def on_update(self):
		from frappe.utils import today
		
		# Automatically call the next patient in the queue if current moves to Diperiksa, Selesai, or Dilewati
		if self.has_value_changed("status") and self.status in ["Diperiksa", "Selesai", "Dilewati"]:
			next_ticket = frappe.get_all(
				"Clinic Queue Ticket",
				filters={"status": "Menunggu", "creation": [">=", today()]},
				order_by="creation asc",
				limit=1
			)
			if next_ticket:
				frappe.db.set_value("Clinic Queue Ticket", next_ticket[0].name, "status", "Dipanggil")

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
