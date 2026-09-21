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
		validate_schedule_vs_appointment_time(frm);
		if (frm.doc.practitioner_schedule_time && frm.doc.practitioner_schedule_time.includes(' - ')) {
			let parts = frm.doc.practitioner_schedule_time.split(' - ');
			if (parts.length === 2) {
				try {
					let [h1, m1] = parts[0].trim().split(':').map(Number);
					let [h2, m2] = parts[1].trim().split(':').map(Number);
					let diff = (h2 * 60 + m2) - (h1 * 60 + m1);
					if (diff > 0) {
						frm.set_value('duration', diff);
					}
				} catch(e) {}
			}
		}
	},
	appointment_time: function(frm) {
		validate_schedule_vs_appointment_time(frm);
	}
});

function validate_schedule_vs_appointment_time(frm) {
	if (frm.doc.practitioner_schedule_time && frm.doc.appointment_time) {
		if (frm.doc.practitioner_schedule_time.includes(' - ')) {
			let parts = frm.doc.practitioner_schedule_time.split(' - ');
			if (parts.length === 2) {
				let to_time = parts[1].trim();
				let app_time = String(frm.doc.appointment_time).trim();
				if (to_time.length === 5) to_time += ':00';
				if (app_time.length === 5) app_time += ':00';

				if (to_time < app_time) {
					frappe.msgprint({
						title: __('Jadwal Dokter Tidak Sesuai'),
						indicator: 'orange',
						message: __('Jadwal dokter ({0}) sudah berakhir dan lebih awal dari waktu pendaftaran ({1}). Silakan pilih jadwal dokter yang sesuai.', [frm.doc.practitioner_schedule_time, app_time])
					});
					frm.set_value('practitioner_schedule_time', '');
				}
			}
		}
	}
}

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
							try {
								let [h1, m1] = res.time_slots[0].from_time.split(':').map(Number);
								let [h2, m2] = res.time_slots[0].to_time.split(':').map(Number);
								let diff = (h2 * 60 + m2) - (h1 * 60 + m1);
								if (diff > 0) {
									frm.set_value('duration', diff);
								}
							} catch(e) {}
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


