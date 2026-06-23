import frappe

def run():
    frappe.init(site="clinic-satusehat.site")
    frappe.connect()

    logs = frappe.get_all('Error Log', limit=3, order_by='creation desc', fields=['method', 'error'])
    for log in logs:
        print(f"Method: {log.method}")
        print(f"Error: {log.error}")
        print("-" * 50)
