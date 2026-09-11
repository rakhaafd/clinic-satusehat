// Copyright (c) 2026, Rakha and contributors
// For license information, please see license.txt

frappe.ui.form.on('Vital Signs', {
	setup: function(frm) {
		frm.set_query('queue_registration', function() {
			return {
				filters: {
					status_nurse: ['!=', 'Completed']
				}
			};
		});
	},
	refresh: function(frm) {
		frm.set_query('queue_registration', function() {
			return {
				filters: {
					status_nurse: ['!=', 'Completed']
				}
			};
		});
	},
	queue_registration: function(frm) {
		if (frm.doc.queue_registration) {
			frappe.db.get_doc('Queue Registration', frm.doc.queue_registration).then(qr => {
				if (qr && qr.patient) {
					frm.set_value('patient', qr.patient);
				} else if (qr && qr.reference_patient_registration) {
					frappe.db.get_doc('Patient Registration', qr.reference_patient_registration).then(rp => {
						if (rp && rp.patient) {
							frm.set_value('patient', rp.patient);
						}
					});
				}
			});
		}
	}
});
