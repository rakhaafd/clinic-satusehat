// Copyright (c) 2026, Rakha and contributors
// For license information, please see license.txt

frappe.ui.form.on('Vital Signs', {
	queue_registration: function(frm) {
		if (frm.doc.queue_registration) {
			frappe.db.get_doc('Queue Registration', frm.doc.queue_registration).then(qr => {
				if (qr && qr.patient) {
					frm.set_value('patient', qr.patient);
				} else if (qr && qr.reference_register_patient) {
					frappe.db.get_doc('Register Patient', qr.reference_register_patient).then(rp => {
						if (rp && rp.patient) {
							frm.set_value('patient', rp.patient);
						}
					});
				}
			});
		}
	}
});
