import frappe
from frappe.utils import add_days, now_datetime

def run():
    frappe.init(site="clinic-satusehat.site")
    frappe.connect()

    yesterday = add_days(now_datetime(), -1)
    
    fields = frappe.get_all('Custom Field', 
        filters={'creation': ['>=', yesterday]}, 
        fields=['name', 'dt', 'fieldname', 'creation', 'owner']
    )
    
    print("Custom fields created in the last 24 hours:")
    for f in fields:
        print(f)
