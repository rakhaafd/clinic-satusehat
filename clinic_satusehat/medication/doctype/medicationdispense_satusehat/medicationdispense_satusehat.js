// Copyright (c) 2026, rakha and contributors
// For license information, please see license.txt

frappe.ui.form.on("MedicationDispense SatuSehat", {
	refresh: function(frm) {
		if (frm.doc.status === "Valid" && frm.doc.items && frm.doc.items.length > 0 && !frm.is_new()) {
			frm.add_custom_button(__("Send to SatuSehat"), function() {
				frappe.call({
					method: "clinic_satusehat.medication.doctype.medicationdispense_satusehat.medicationdispense_satusehat.send_to_satusehat",
					args: {
						docname: frm.doc.name
					},
					freeze: true,
					freeze_message: "Sending to SatuSehat...",
					callback: function(r) {
						if (r.message) {
							frm.reload_doc();
							if(r.message.status == 201 || r.message.status == 200) {
								frappe.msgprint({
									title: __('Success'),
									indicator: 'green',
									message: __('Data berhasil terkirim dengan status ' + r.message.status)
								});
							} else if (r.message.status == 206) {
								frappe.msgprint({
									title: __('Warning'),
									indicator: 'orange',
									message: r.message.message
								});
							} else {
								frappe.msgprint({
									title: __('Error'),
									indicator: 'red',
									message: r.message.message
								});
							}
						}
					}
				});
			}).addClass("btn-primary");
		}
	},
	fetch_drugs_btn: function(frm) {
		if (!frm.doc.medication_request_satusehat) {
			frappe.msgprint("Silakan pilih MedicationRequest SatuSehat terlebih dahulu.");
			return;
		}
		
		frappe.call({
			method: "fetch_drugs_from_request",
			doc: frm.doc,
			freeze: true,
			freeze_message: "Menarik data resep...",
			callback: function(r) {
				frm.reload_doc();
			}
		});
	}
});
