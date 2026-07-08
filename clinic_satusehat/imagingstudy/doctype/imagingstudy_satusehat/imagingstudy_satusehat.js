// Copyright (c) 2026, rakha and contributors
// For license information, please see license.txt

frappe.ui.form.on("ImagingStudy SatuSehat", {
	refresh: function(frm) {
		if (frm.doc.status === "Valid" && !frm.doc.satusehat_id && !frm.is_new()) {
			frm.add_custom_button(__("Send to SatuSehat"), function() {
				frappe.call({
					method: "clinic_satusehat.imagingstudy.doctype.imagingstudy_satusehat.imagingstudy_satusehat.send_to_satusehat",
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
	}
});
