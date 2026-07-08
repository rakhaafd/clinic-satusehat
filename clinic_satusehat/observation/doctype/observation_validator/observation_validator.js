// Copyright (c) 2026, rakha and contributors
// For license information, please see license.txt

frappe.ui.form.on("Observation Validator", {
	refresh: function(frm) {
		if (frm.doc.status === "Valid") {
			frm.set_df_property("status", "read_only", 1);
		}
	}
});
