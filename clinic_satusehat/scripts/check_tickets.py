import frappe

def run():
    frappe.init(site="clinic-satusehat.site")
    frappe.connect()

    tickets = frappe.get_all('Clinic Queue Ticket', fields=['name', 'status', 'encounter_ref'])
    for t in tickets:
        print(f"Ticket: {t.name}, Status: {t.status}, Encounter: {t.encounter_ref}")
