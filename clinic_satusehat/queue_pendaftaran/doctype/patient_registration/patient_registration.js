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
	},
	practitioner: function(frm) {
		check_and_set_doctor_schedule(frm);
	},
	appointment_date: function(frm) {
		check_and_set_doctor_schedule(frm);
	},
	practitioner_schedule_time: function(frm) {
		if (frm.doc.practitioner_schedule_time) {
			let time_val = frm.doc.practitioner_schedule_time.split(' - ')[0].trim();
			if (time_val) {
				frm.set_value('appointment_time', time_val);
			}
		}
	}
});

function check_and_set_doctor_schedule(frm) {
	if (frm.doc.practitioner && frm.doc.appointment_date) {
		frappe.call({
			method: 'clinic_satusehat.api.appointment.get_practitioner_available_slots',
			args: {
				practitioner: frm.doc.practitioner,
				date: frm.doc.appointment_date
			},
			callback: function(r) {
				if (r.message) {
					let res = r.message;
					if (!res.has_schedule_on_this_day) {
						let days = (res.practice_days || []).join(', ') || 'Belum diatur';
						frm.set_df_property('practitioner_schedule_time', 'options', '');
						frm.set_value('practitioner_schedule_time', '');
						frappe.msgprint({
							title: __('Dokter Tidak Berpraktek'),
							indicator: 'orange',
							message: __('Dokter {0} tidak berpraktek pada hari {1} ({2}).<br>Hari berpraktek: <b>{3}</b>', 
								[res.practitioner_name || frm.doc.practitioner, res.day_of_week, frm.doc.appointment_date, days])
						});
					} else if (res.time_slots && res.time_slots.length > 0) {
						let options = [''];
						res.time_slots.forEach(slot => {
							options.push(`${slot.from_time} - ${slot.to_time}`);
						});
						frm.set_df_property('practitioner_schedule_time', 'fieldtype', 'Select');
						frm.set_df_property('practitioner_schedule_time', 'options', options.join('\n'));
						
						// Auto select first schedule if not set
						if (!frm.doc.practitioner_schedule_time && options.length > 1) {
							frm.set_value('practitioner_schedule_time', options[1]);
							frm.set_value('appointment_time', res.time_slots[0].from_time);
						}
					}
				}
			}
		});
	} else {
		frm.set_df_property('practitioner_schedule_time', 'options', '');
		frm.set_value('practitioner_schedule_time', '');
	}
}


