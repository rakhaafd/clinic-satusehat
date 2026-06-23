import frappe

def run():
    frappe.init(site="clinic-satusehat.site")
    frappe.connect()

    try:
        # Check if the server script exists
        script_name = "Auto Create Encounter"
        if frappe.db.exists("Server Script", script_name):
            frappe.delete_doc("Server Script", script_name, ignore_permissions=True, force=1)
            frappe.db.commit()
            print(f"Successfully deleted Server Script: {script_name}")
        else:
            print(f"Server Script '{script_name}' not found. Let's list all server scripts.")
            scripts = frappe.get_all("Server Script", pluck="name")
            print("Existing server scripts:", scripts)
            
            # Delete any that might be the auto link encounter
            for s in scripts:
                if 'encounter' in s.lower() or 'auto' in s.lower():
                    frappe.delete_doc("Server Script", s, ignore_permissions=True, force=1)
                    print(f"Deleted related Server Script: {s}")
            frappe.db.commit()
            
    except Exception as e:
        print(f"Error: {e}")
