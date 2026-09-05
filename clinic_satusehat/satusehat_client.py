import frappe
import requests
import json

def get_satusehat_headers():
	"""
	Fetch OAuth 2.0 Access Token from SATUSEHAT auth endpoint.
	"""
	client_id = frappe.conf.get("satusehat_client_id")
	client_secret = frappe.conf.get("satusehat_client_secret")
	auth_url = frappe.conf.get("satusehat_auth_url") or "https://api-satusehat-stg.dto.kemkes.go.id/oauth2/v1"

	if not client_id or not client_secret:
		frappe.throw("SATUSEHAT Client ID dan Client Secret belum dikonfigurasi di site_config.json.")

	token_url = f"{auth_url}/accesstoken?grant_type=client_credentials"
	data = {"client_id": client_id, "client_secret": client_secret}

	try:
		res = requests.post(token_url, data=data, timeout=15)
		if res.status_code == 200:
			token = res.json().get("access_token")
			return {
				"Authorization": f"Bearer {token}",
				"Content-Type": "application/json"
			}
		frappe.throw(f"Gagal mendapatkan Token SATUSEHAT: {res.text}")
	except Exception as e:
		frappe.throw(f"Error Koneksi Autentikasi SATUSEHAT: {str(e)}")

def get_base_url():
	"""
	Get Base FHIR API URL from site_config.json or default to staging.
	"""
	return frappe.conf.get("satusehat_base_url") or "https://api-satusehat-stg.dto.kemkes.go.id/fhir-r4/v1"

def get_organization_id():
	"""
	Get Organization ID / IHS Organization ID from site_config.json.
	"""
	return frappe.conf.get("satusehat_organization_id") or ""

def send_resource(doc, resource_type=None, payload_field=None):
	"""
	Centralized method to send FHIR payload (single or array of resources) to SATUSEHAT API,
	log responses to SatuSehat API Log, and update document fields.
	"""
	payload_str = None
	if payload_field and hasattr(doc, payload_field):
		payload_str = getattr(doc, payload_field)
	elif hasattr(doc, "generated_payload") and doc.generated_payload:
		payload_str = doc.generated_payload
	elif hasattr(doc, "payload_json") and doc.payload_json:
		payload_str = doc.payload_json

	if not payload_str:
		frappe.throw("Payload JSON kosong. Silakan simpan (Save) dokumen terlebih dahulu untuk membuat payload!")

	try:
		payload_data = json.loads(payload_str)
	except Exception as e:
		frappe.throw(f"Format JSON Payload tidak valid: {str(e)}")

	is_list = isinstance(payload_data, list)
	items = payload_data if is_list else [payload_data]

	base_url = get_base_url()
	headers = get_satusehat_headers()

	results = []
	satusehat_ids = []
	all_success = True

	for item in items:
		target_resource = resource_type or item.get("resourceType")
		if not target_resource:
			frappe.throw("Resource Type tidak ditemukan pada Payload JSON.")

		endpoint = f"{base_url}/{target_resource}"
		try:
			resp = requests.post(endpoint, json=item, headers=headers, timeout=60)
			res_data = {"status_code": resp.status_code, "response": resp.text}
			results.append(res_data)

			satusehat_id = ""
			if resp.status_code in [200, 201]:
				try:
					r_json = resp.json()
					if "id" in r_json:
						satusehat_id = r_json["id"]
						satusehat_ids.append(satusehat_id)
				except Exception:
					pass
			else:
				all_success = False

			# Log to SatuSehat API Log
			try:
				log_doc = frappe.get_doc({
					"doctype": "SatuSehat API Log",
					"reference_doctype": doc.doctype,
					"reference_doc": doc.name,
					"resource_type": target_resource,
					"satusehat_id": satusehat_id,
					"status_code": resp.status_code,
					"response_json": resp.text
				})
				log_doc.insert(ignore_permissions=True)
			except Exception as log_err:
				frappe.log_error(f"Gagal mencatat SatuSehat API Log: {str(log_err)}")

		except Exception as e:
			all_success = False
			results.append({"error": str(e)})

	summary_str = json.dumps(results, indent=2) if is_list else f"STATUS CODE: {results[0].get('status_code')}\n\n{results[0].get('response') or results[0].get('error')}"
	
	if hasattr(doc, "api_response"):
		frappe.db.set_value(doc.doctype, doc.name, "api_response", summary_str)

	if satusehat_ids:
		if hasattr(doc, "satusehat_ids"):
			frappe.db.set_value(doc.doctype, doc.name, "satusehat_ids", ", ".join(satusehat_ids))
		elif hasattr(doc, "satusehat_id"):
			frappe.db.set_value(doc.doctype, doc.name, "satusehat_id", satusehat_ids[0])

	satusehat_id = satusehat_ids[0] if satusehat_ids else ""
	return {"status": 201 if all_success else 400, "message": summary_str, "satusehat_ids": satusehat_ids, "satusehat_id": satusehat_id}
