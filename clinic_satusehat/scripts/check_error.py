import frappe

def get_latest_error():
    records = frappe.get_all('Khanza SatuSehat Sync Record', fields=['name', 'sync_status', 'error_message', 'fhir_payload'], order_by='creation desc', limit=1)
    if records:
        print(f"Name: {records[0].name}")
        print(f"Status: {records[0].sync_status}")
        print(f"Error: {records[0].error_message}")
    else:
        print("No records found.")
