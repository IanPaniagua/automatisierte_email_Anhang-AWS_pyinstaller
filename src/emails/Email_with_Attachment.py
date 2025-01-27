import re

class EmailWithAttachments:
    def __init__(self, uid, subject, sender, date, attachments):
        """
        Initialize an email object with metadata and attachments.
        
        Args:
            uid (str): The UID of the email.
            subject (str): The subject of the email.
            sender (str): The sender of the email.
            date (str): The date the email was sent.
            attachments (list): A list of dictionaries with attachment metadata.
        """
        self.uid = uid
        self.subject = subject
        self.sender = sender
        self.date = date
        self.attachments = [
            {
                "file_name": attachment.get("file_name"),
                "path": attachment.get("path"),
                "invoice_number": None,
                "doc_type": "UNKNOWN",
                "prefix": None,
                "status": "pending",
                "verw_nr": None,
                "eigentümer": None,
            }
            for attachment in attachments
        ]


    def __repr__(self):
        return f"EmailWithAttachments(uid={self.uid}, subject={self.subject}, sender={self.sender}, date={self.date}, attachments={len(self.attachments)} files)"