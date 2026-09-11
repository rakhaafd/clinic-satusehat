// Copyright (c) 2026, Rakha and contributors
// For license information, please see license.txt

frappe.ui.form.on('Patient Registration', {
	refresh: function(frm) {
		if (!frm.is_new()) {
			frm.add_custom_button(__('Patient Encounter'), function() {
				frappe.model.open_mapped_doc({
					method: 'clinic_satusehat.queue_pendaftaran.doctype.patient_registration.patient_registration.make_patient_encounter',
					frm: frm
				});
			}, __('Create'));
		}
	}
});
