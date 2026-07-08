// Copyright (c) 2026, rakha and contributors
// For license information, please see license.txt

frappe.listview_settings['ClinicalImpression Validator'] = {
	get_indicator: function(doc) {
		if (doc.status === "Waiting") {
			return [__("Waiting"), "orange", "status,=,Waiting"];
		} else if (doc.status === "Valid") {
			return [__("Valid"), "green", "status,=,Valid"];
		} else if (doc.status === "Rejected") {
			return [__("Rejected"), "red", "status,=,Rejected"];
		}
	}
};
