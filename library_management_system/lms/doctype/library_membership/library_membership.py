# Copyright (c) 2024, lms and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class LibraryMembership(Document):
	
	def before_submit(self):
		member_exist = frappe.db.exists("Library Membership",{"library_member":self.library_member,"docstatus":1,"to_date":(">", self.from_date)})
		if member_exist:
			frappe.throw("An active membership already exist for this member.")

		loan_period = frappe.db.get_single_value("Library Settings", "loan_period")
		self.to_date = frappe.utils.add_days(self.from_date, loan_period or 30)
