import frappe

def run():
    frappe.init(site="clinic-satusehat.site")
    frappe.connect()

    script_name = "Clinic Queue Ticket Client Script"
    if frappe.db.exists("Client Script", script_name):
        doc = frappe.get_doc("Client Script", script_name)
        doc.script = """
frappe.ui.form.on('Clinic Queue Ticket', {
    refresh: function(frm) {
        // Hanya tampilkan tombol jika statusnya Diperiksa dan belum ada referensi Encounter
        if (frm.doc.status === 'Diperiksa' && !frm.doc.encounter_ref) {
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
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        print("Updated Client Script")
