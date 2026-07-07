frappe.ui.form.on("SatuSehat Payload Generator", {
	refresh: function(frm) {
		if (!frm.is_new() && frm.doc.generated_payload) {
			frm.add_custom_button(__("Send to SatuSehat"), function() {
				frappe.call({
					method: "clinic_satusehat.queue_core.doctype.satusehat_payload_generator.satusehat_payload_generator.send_to_satusehat",
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
									message: __('Gagal mengirim dengan status ' + r.message.status)
								});
							}
						}
					}
				});
			}).addClass("btn-primary");
		}
	},
	
	resource_type: function(frm) {
		if (frm.doc.resource_type == "Encounter") {
			frm.set_df_property('encounter_id', 'hidden', 1);
			frm.set_df_property('diagnostic_code', 'hidden', 1);
			frm.set_df_property('observation_value', 'hidden', 1);
			frm.set_df_property('patient_encounter', 'hidden', 0);
		} else if (frm.doc.resource_type == "Condition" || frm.doc.resource_type == "Procedure") {
			frm.set_df_property('encounter_id', 'hidden', 0);
			frm.set_df_property('diagnostic_code', 'hidden', 0);
			frm.set_df_property('observation_value', 'hidden', 1);
			frm.set_df_property('patient_encounter', 'hidden', 0);
		} else if (frm.doc.resource_type == "Observation") {
			frm.set_df_property('encounter_id', 'hidden', 0);
			frm.set_df_property('diagnostic_code', 'hidden', 1);
			frm.set_df_property('observation_value', 'hidden', 0);
			frm.set_df_property('patient_encounter', 'hidden', 0);
		} else if (frm.doc.resource_type == "Composition" || frm.doc.resource_type == "MedicationRequest" || frm.doc.resource_type == "MedicationDispense") {
			frm.set_df_property('encounter_id', 'hidden', 0);
			frm.set_df_property('diagnostic_code', 'hidden', 1);
			frm.set_df_property('observation_value', 'hidden', 1);
			frm.set_df_property('patient_encounter', 'hidden', 0);
		} else if (frm.doc.resource_type == "Medication") {
			frm.set_df_property('encounter_id', 'hidden', 1);
			frm.set_df_property('diagnostic_code', 'hidden', 1);
			frm.set_df_property('observation_value', 'hidden', 1);
			frm.set_df_property('patient_encounter', 'hidden', 0);
		}
	},
	
	patient_encounter: function(frm) {
		if(frm.doc.patient_encounter) {
			frappe.call({
				method: "frappe.client.get",
				args: {
					doctype: "Patient Encounter",
					name: frm.doc.patient_encounter
				},
				callback: function(r) {
					if(r.message) {
						let patient = r.message.patient;
						let practitioner = r.message.practitioner;
						
						if(patient) {
							frappe.db.get_value('Patient', patient, 'satusehat_id')
							.then(r => {
								if(r.message.satusehat_id) {
									frm.set_value('patient_ihs', r.message.satusehat_id);
								} else {
									frappe.show_alert("Pasien belum memiliki IHS Number");
								}
							});
						}
						
						if(practitioner) {
							frappe.db.get_value('Healthcare Practitioner', practitioner, 'satusehat_id')
							.then(r => {
								if(r.message.satusehat_id) {
									frm.set_value('practitioner_ihs', r.message.satusehat_id);
								} else {
									frappe.show_alert("Dokter belum memiliki IHS Number");
								}
							});
						}
					}
				}
			});
		}
	}
});
