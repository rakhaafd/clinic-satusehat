// Copyright (c) 2026, Rakha and contributors
// For license information, please see license.txt

frappe.ui.form.on('Patient Encounter', {
	patient_registration: function(frm) {
		if (frm.doc.patient_registration) {
			frappe.db.get_doc('Patient Registration', frm.doc.patient_registration).then(pr => {
				if (pr) {
					if (pr.patient) frm.set_value('patient', pr.patient);
					if (pr.patient_name) frm.set_value('patient_name', pr.patient_name);
					if (pr.patient_sex) frm.set_value('patient_sex', pr.patient_sex);
					if (pr.patient_age) frm.set_value('patient_age', pr.patient_age);
					if (pr.inpatient_record) frm.set_value('inpatient_record', pr.inpatient_record);
					if (pr.company) frm.set_value('company', pr.company);
					if (pr.department) frm.set_value('medical_department', pr.department);
					if (pr.appointment_date) frm.set_value('encounter_date', pr.appointment_date);
					if (pr.appointment_time) frm.set_value('encounter_time', pr.appointment_time);
				}
			});
		}
	}
});
