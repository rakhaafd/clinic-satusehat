import frappe

def get_vitals():
    docs = frappe.get_all('Vital Signs', fields=['name', 'encounter', 'bp_systolic', 'bp_diastolic', 'bp', 'signs_date', 'signs_time'])
    for d in docs:
        print(d)
