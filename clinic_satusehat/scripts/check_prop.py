import frappe

def get_prop_setter():
    props = frappe.get_all('Property Setter', filters={'doc_type': 'Vital Signs', 'field_name': 'encounter'}, fields=['name', 'property', 'value'])
    for p in props:
        print(p)
