import frappe
def run():
    errs = frappe.get_all("Error Log", fields=["method", "error", "creation"], limit=3, order_by="creation desc")
    for e in errs:
        print(f"[{e.creation}] {e.method}")
        print(e.error)
        print("-" * 50)
