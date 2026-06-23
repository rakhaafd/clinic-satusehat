import frappe

def run():
    val = frappe.db.get_single_value('Healthcare Settings', 'default_item_group')
    print(f"Default Item Group in Healthcare Settings is: {val}")
