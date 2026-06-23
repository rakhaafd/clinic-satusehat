
// Copyright (c) 2026, rakha and contributors
// For license information, please see license.txt

frappe.ui.form.on("Clinic Queue Ticket", {
	refresh(frm) {
		frm.trigger("fetch_encounter");
	},
	status(frm) {
		if (frm.doc.status === "Selesai") {
			frm.trigger("fetch_encounter");
		}
	},
	fetch_encounter(frm) {
		// Hanya fetch jika encounter_ref masih kosong dan nama pasien ada
		if (!frm.doc.encounter_ref && frm.doc.patient_name) {
			// Hanya fetch jika statusnya Diperiksa atau Selesai
			if (["Diperiksa", "Selesai"].includes(frm.doc.status)) {
				frappe.call({
					method: "frappe.client.get_list",
					args: {
						doctype: "Patient Encounter",
						filters: {
							patient: frm.doc.patient_name,
							creation: [">=", frappe.datetime.get_today()]
						},
						order_by: "creation desc",
						limit_page_length: 1
					},
					callback: function(r) {
						if (r.message && r.message.length > 0) {
							frm.set_value("encounter_ref", r.message[0].name);
							frappe.show_alert({message: 'Patient Encounter berhasil ditautkan secara otomatis!', indicator: 'green'});
						}
					}
				});
			}
		}
	}
});
