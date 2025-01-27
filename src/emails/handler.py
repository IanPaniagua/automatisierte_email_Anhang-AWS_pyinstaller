import email
from email.policy import default
from config.config import load_config, save_config
import os
from .Email_with_Attachment import EmailWithAttachments
import json
from config.loggin_config import logger

ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg"}

def fetch_email_by_uid(mail, uid):
    try:
        mail.select("INBOX", readonly=True)
        status, msg_data = mail.uid("FETCH", uid, "(RFC822)")
        if status != "OK":
            logger.warning(f"Error fetching email with UID {uid}")
            return None

        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1], policy=default)
                return msg
        return None
    except Exception as e:
        logger.error(f"Error retrieving email by UID {uid}: {e}")
        return None

def search_emails(mail, criteria):
    """
    Searches for emails matching the given criteria.

    Args:
        mail (IMAP4_SSL): IMAP mail object.
        criteria (str): Search criteria.

    Returns:
        tuple: (List of UIDs, max UID found)
    """
    try:
        status, count = mail.select("INBOX", readonly=True)
        logger.info(f"Searching for emails in INBOX...")
        status, data = mail.uid("SEARCH", None, criteria)

        if status != "OK":
            logger.warning(f"SEARCH failed with status: {status}")
            return [], 0

        if not data or not data[0]:
            logger.info("No emails matched the criteria.")
            return [], 0

        uids = [int(uid.decode('utf-8')) for uid in data[0].split()]
        max_uid = max(uids) if uids else 0
        logger.info(f"UIDs found: {uids}, Max UID: {max_uid}")
        return uids, max_uid

    except Exception as e:
        logger.error(f"Error searching emails: {e}")
        return [], 0
    
def process_email(msg, uid):
    """
    Processes an email and saves its attachments.

    Args:
        msg (EmailMessage): The email message to process.
        uid (str): The UID of the email.

    Returns:
        EmailWithAttachments: Object containing the email's metadata and raw attachments.
    """
    if msg:
        subject = msg['subject']
        sender = msg['from']
        date = msg['date']

        attachments = []
        for part in msg.iter_attachments():
            filename = part.get_filename()
            if filename:
                extension = filename.rsplit(".", 1)[-1].lower()
                if extension in ALLOWED_EXTENSIONS:
                    content = part.get_payload(decode=True)
                    saved_path = save_attachment_into_folder(content, filename)
                    if saved_path:
                        attachments.append({"filename": filename, "path": saved_path})
                else:
                    logger.warning(f"Attachment skipped: {filename} (Invalid extension)")

        email_obj = EmailWithAttachments(uid, subject, sender, date, attachments)
        logger.info(f"Processed Email: UID {uid}, Subject: {subject}, Sender: {sender}")
        return email_obj
    else:
        logger.warning(f"Email with UID {uid} not found.")
        return None

def process_emails_since(mail, last_uid):
    """
    Download and process all emails since the last UID and return a list of EmailWithAttachments.

    Args:
        mail (IMAP4_SSL): The mail object to interact with the IMAP server.
        last_uid (int): The last processed UID.

    Returns:
        list: A list of EmailWithAttachments objects.
    """
    emails = []
    try:
        criteria = f"UID {last_uid + 1}:*"
        logger.info(f"Searching for emails with criteria: {criteria}")
        uids, server_max_uid = search_emails(mail, criteria)

        if not uids:
            logger.info("No new emails found.")
            return emails

        # Update max UID in config
        config = load_config()
        if server_max_uid > config.get("max_uid", 0):
            config["max_uid"] = server_max_uid
            save_config(config)
            logger.info(f"Updated max UID in config to {server_max_uid}")

        # Filter UIDs to ensure they are greater than last_uid
        valid_uids = [uid for uid in uids if uid > last_uid]
        logger.info(f"Valid UIDs to process: {valid_uids}")

        if not valid_uids:
            logger.info("No valid new emails to process after filtering.")
            return emails

        for uid in valid_uids:
            logger.info(f"Fetching email with UID (SINCE) {uid}...")
            msg = fetch_email_by_uid(mail, str(uid))
            if msg:
                email_obj = process_email(msg, str(uid))
                if email_obj:
                    emails.append(email_obj)
            else:
                logger.warning(f"Email with UID {uid} could not be fetched.")

        logger.info(f"Processed {len(emails)} new emails.")
        return emails

    except Exception as e:
        logger.error(f"Error downloading emails: {e}")
        return emails

def save_attachment_into_folder(content, filename, folder_path=None):
    """
    Saves an email attachment to the specified or default folder.

    Args:
        content (bytes): The binary content of the attachment.
        filename (str): The name of the attachment file.
        folder_path (str): Optional folder where the attachment will be saved. Defaults to attachment_folder from config.

    Returns:
        str: The full path of the saved attachment file.
    """
    try:
        if not folder_path:
            config = load_config()
            folder_path = config.get("attachment_folder", "attachments")

        os.makedirs(folder_path, exist_ok=True)
        logger.info(f"Folder ensured: {folder_path}")

        file_path = os.path.join(folder_path, filename)

        with open(file_path, "wb") as f:
            f.write(content)
        logger.info(f"Attachment successfully saved to: {file_path}")

        return file_path
    except Exception as e:
        logger.error(f"An error occurred while saving the attachment: {e}")
        return None

import os

#TODO:TEST
#TODO: replace with SQLite
def save_emails_to_json_split(email_objs, output_folder, max_entries_per_file=1000):
    """
    Appends email objects to multiple JSON files, splitting them when they exceed a certain number of entries.

    Args:
        email_objs (list): List of EmailWithAttachments objects.
        output_folder (str): Folder where the JSON files will be saved.
        max_entries_per_file (int): Maximum number of entries per JSON file.
    """
    os.makedirs(output_folder, exist_ok=True)  # Ensure the output folder exists

    # Convert EmailWithAttachments objects to dictionaries
    def email_to_dict(email):
        return {
            "uid": email.uid,
            "subject": email.subject,
            "sender": email.sender,
            "date": email.date,
            "attachments": email.attachments,
        }

    # Convert new emails to dictionaries
    new_emails = [email_to_dict(email) for email in email_objs]

    # Find the last part file or create a new one
    existing_files = sorted(
        [f for f in os.listdir(output_folder) if f.startswith("processed_emails_part")],
        key=lambda x: int(x.split("part")[-1].split(".json")[0])
    )
    
    if existing_files:
        # Load the last file to append data
        last_file = os.path.join(output_folder, existing_files[-1])
        with open(last_file, "r", encoding="utf-8") as json_file:
            existing_data = json.load(json_file)

        # Append new data to the last file
        updated_data = existing_data + new_emails

        if len(updated_data) > max_entries_per_file:
            # Split data if it exceeds the max entries
            excess_data = updated_data[max_entries_per_file:]
            updated_data = updated_data[:max_entries_per_file]
            with open(last_file, "w", encoding="utf-8") as json_file:
                json.dump(updated_data, json_file, ensure_ascii=False, indent=4)
            print(f"Updated {len(updated_data)} emails in {last_file}")

            # Save remaining data to a new file
            save_emails_to_json_split(excess_data, output_folder, max_entries_per_file)
        else:
            # Save the updated data back to the same file
            with open(last_file, "w", encoding="utf-8") as json_file:
                json.dump(updated_data, json_file, ensure_ascii=False, indent=4)
            print(f"Appended {len(new_emails)} emails to {last_file}")
    else:
        # No existing files, create the first file
        file_path = os.path.join(output_folder, "processed_emails_part1.json")
        with open(file_path, "w", encoding="utf-8") as json_file:
            json.dump(new_emails, json_file, ensure_ascii=False, indent=4)
        print(f"Created {file_path} with {len(new_emails)} emails")

