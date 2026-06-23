import frappe

def run():
    frappe.init(site="clinic-satusehat.site")
    frappe.connect()

    script_name = "Clinic Queue Ticket Client Script"
    if frappe.db.exists("Client Script", script_name):
        frappe.delete_doc("Client Script", script_name)
        
    script_content = """
frappe.ui.form.on('Clinic Queue Ticket', {
    refresh: function(frm) {
        // Hanya tampilkan tombol jika statusnya bukan Selesai dan belum ada referensi Encounter
        if (frm.doc.status !== 'Selesai' && frm.doc.status !== 'Dilewati' && !frm.doc.encounter_ref) {
            frm.add_custom_button(__('Create Patient Encounter'), function() {
                frappe.new_doc('Patient Encounter', {
                    patient: frm.doc.patient_name,
                    practitioner: frm.doc.practitioner
                });
            }, __('Actions'));
        }
    }
});
"""

    doc = frappe.get_doc({
        "doctype": "Client Script",
        "dt": "Clinic Queue Ticket",
        "name": script_name,
        "module": "Queue Poli",
        "script": script_content,
        "enabled": 1
    })
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    print("Client Script created successfully.")
