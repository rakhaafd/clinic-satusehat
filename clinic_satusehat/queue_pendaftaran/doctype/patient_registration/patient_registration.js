// Copyright (c) 2026, Rakha and contributors
// For license information, please see license.txt

frappe.ui.form.on('Patient Registration', {
	setup: function(frm) {
		frm.set_query('practitioner', function() {
			let filters = {
				'status': 'Active'
			};
			if (frm.doc.department) {
				filters['department'] = frm.doc.department;
			}
			return { filters: filters };
		});
	},
	refresh: function(frm) {
		if (!frm.is_new()) {
			frm.add_custom_button(__('Patient Encounter'), function() {
				frappe.model.open_mapped_doc({
					method: 'clinic_satusehat.queue_pendaftaran.doctype.patient_registration.patient_registration.make_patient_encounter',
					frm: frm
				});
			}, __('Create'));
		}
	},
	department: function(frm) {
		if (frm.doc.practitioner && frm.doc.department) {
			frappe.db.get_value('Healthcare Practitioner', frm.doc.practitioner, 'department', (r) => {
				if (r && r.department !== frm.doc.department) {
					frm.set_value('practitioner', '');
				}
			});
		}
	}
});
