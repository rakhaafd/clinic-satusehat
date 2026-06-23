frappe.listview_settings['Clinic Queue Ticket'] = {
    onload: function(listview) {
        listview.page.add_action_item(__('Create Patient Encounter'), function() {
            let checked_items = listview.get_checked_items();
            if (checked_items.length !== 1) {
                frappe.msgprint(__('Pilih tepat satu tiket antrean yang berstatus Diperiksa.'));
                return;
            }
            
            let item = checked_items[0];
            if (item.status !== 'Diperiksa') {
                frappe.msgprint(__('Tombol ini hanya berlaku untuk tiket berstatus "Diperiksa".'));
                return;
            }
            
            frappe.new_doc('Patient Encounter', {
                patient: item.patient_name,
                practitioner: item.practitioner
            });
        });
    }
};
