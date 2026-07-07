import frappe

class PayloadBuilder:
    def build(self, doc):
        raise NotImplementedError("Subclasses must implement build()")
