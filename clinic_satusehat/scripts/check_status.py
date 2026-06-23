import frappe

def run():
    frappe.init(site="clinic-satusehat.site")
    frappe.connect()

    logs = frappe.get_all('Error Log', limit=2, order_by='creation desc', fields=['method', 'error'])
    for log in logs:
        print(f"Error: {log.error[:500]}")
    
    tickets = frappe.get_all('Clinic Queue Ticket', fields=['name', 'status', 'encounter_ref'])
    print("Tickets:", tickets)
    
    pharmacy = frappe.get_all('Pharmacy Queue Ticket', fields=['name'])
    print("Pharmacy:", pharmacy)
