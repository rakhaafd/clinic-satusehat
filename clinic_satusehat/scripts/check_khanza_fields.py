import frappe

def run():
    frappe.init(site="clinic-satusehat.site")
    frappe.connect()

    fields = frappe.get_all('Custom Field', 
        fields=['name', 'dt', 'fieldname', 'creation', 'owner']
    )
    
    print("All Custom fields matching 'khanza' or created recently:")
    found = False
    for f in fields:
        if 'khanza' in f.dt.lower() or 'khanza' in f.fieldname.lower() or 'khanza' in f.name.lower():
            print(f)
            found = True
            
    if not found:
        print("No custom fields with 'khanza' found.")
