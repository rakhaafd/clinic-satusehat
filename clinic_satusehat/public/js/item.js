frappe.ui.form.on('Item', {
	refresh: function(frm) {
		if (frm.doc.kfa_code && !frm.doc.satusehat_id && !frm.is_new()) {
			frm.add_custom_button(__('Send to SatuSehat'), function() {
				frappe.call({
					method: 'clinic_satusehat.api.register_item_medication',
					args: {
						item_code: frm.doc.item_code
					},
					freeze: true,
					freeze_message: "Mendaftarkan Obat ke SatuSehat...",
					callback: function(r) {
						if (r.message && r.message.status === "success") {
							frm.reload_doc();
							frappe.msgprint({
								title: __('Success'),
								indicator: 'green',
								message: r.message.message
							});
						}
					}
				});
			}, __('SatuSehat')).addClass('btn-primary');
		}
	}
});
