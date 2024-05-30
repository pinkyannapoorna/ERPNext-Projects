import frappe
from frappe.model.document import Document
from frappe.model.docstatus import DocStatus


class LibraryTransaction(Document):

    def validate(self):
        if self.is_new() and self.type == "Issue":
            self.active = 1
   
    def validate_membership(self):
        valid_membership = frappe.db.exists(
            "Library Membership",
            {
                "library_member": self.library_member,
                "docstatus": DocStatus.submitted(),
                "from_date": ("<", self.date),
                "to_date": (">", self.date),
            },
        )
        if not valid_membership:
            frappe.throw("The member does not have a valid membership")


    def before_submit(self):
        if self.type == "Issue":
            self.validate_membership()
            self.validate_no_of_qty()
            self.validate_maximum_limit()
            self.validate_issued_article()
        else:
            self.validate_return()

    def validate_issued_article(self):
        count = frappe.db.count(
            "Library Transaction",
            {"library_member": self.library_member, "type": "Issue", "docstatus": 1,"active": 1,'article':self.article},
        )
        if count != 0:
            frappe.throw("This Article already issued to this member.")

    
    def validate_no_of_qty(self):
        article = frappe.get_doc("Article", self.article)
        if article.total_no_of_articles_available == article.issued_articles:
            frappe.throw("This Article Quantity currently not available to issue.")

    def validate_maximum_limit(self):
        max_articles = frappe.db.get_single_value("Library Settings", "max_articles")
        count = frappe.db.count(
            "Library Transaction",
            {"library_member": self.library_member, "type": "Issue", "docstatus": 1,"active": 1},
        )
        if count >= max_articles:
            frappe.throw("Maximum limit reached for issuing articles")

    def on_submit(self):
        self.update_issued_qty()

    def update_issued_qty(self):
        if self.type == "Issue":
            article = frappe.get_doc("Article", self.article)
            article.issued_articles += 1
            if article.total_no_of_articles_available == article.issued_articles:
                article.status = "Issued"
            article.save()

        if self.type == "Return":
            lt_issued_doc = frappe.get_doc("Library Transaction",self.library_transaction_issued_id)
            lt_issued_doc.active = 0
            lt_issued_doc.save()
            article = frappe.get_doc("Article", self.article)
            article.issued_articles -= 1
            if article.issued_articles == 0:
                article.status = "Available"
            article.save()

    def validate_return(self):
        
        article = frappe.get_doc("Article", self.article)
        issued_artcle_transaction = frappe.db.count(
            "Library Transaction",
            {"library_member": self.library_member, "type": "Issue", "docstatus": 1,"active": 1,"article":self.article},
        )
        if issued_artcle_transaction == 0:
            frappe.throw("This Artcle not issued for this member yet to return.")
        if article.issued_articles == 0:
            frappe.throw("This Article not yet issued to return.")