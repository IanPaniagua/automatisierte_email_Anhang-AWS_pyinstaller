import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import time
from imap.connection import get_imap_connection
from emails.handler import process_emails_since, save_emails_to_json_split
from processing.attachments.handler import DefaultFileProcessor, AttachmentProcessor
from processing.attachments.data_loader import load_parameters_from_db
from processing.tracker import get_last_saved_uid, save_last_uid
from config.config import load_config
from utils.resource_path import resource_path
from config.loggin_config import logger

def setup_configuration():
    """
    Ensure the configuration file is set up before running the main program.
    """
    try:
        config = load_config()
        logger.info("Configuration loaded successfully.")

        # Check if max_uid is empty or not set
        if not config.get("max_uid"):
            max_uid = get_max_uid_from_server()
            if max_uid > 0:
                save_last_uid(max_uid)
                logger.info(f"Max UID ({max_uid}) saved to config.json.")
            else:
                logger.info("Unable to determine max UID. Starting from 0.")

    except Exception as e:
        logger.error(f"Error during setup: {e}")

def get_max_uid_from_server():
    """
    Connects to the IMAP server and retrieves the maximum UID.

    Returns:
        int: The maximum UID on the server, or 0 if it cannot be determined.
    """
    try:
        with get_imap_connection() as mail:
            mail.select("INBOX")
            result, data = mail.search(None, "ALL")
            if result == "OK" and data and data[0]:
                max_uid = int(data[0].split()[-1])  # Get the highest UID
                return max_uid
    except Exception as e:
        logger.error(f"Error retrieving max UID from server: {e}")
    return 0

def main():
    setup_configuration()  # Ensure configuration is set up
    config = load_config()

    # Load paths from configuration
    attachment_folder = config.get("attachment_folder", "attachments/")
    destination_folder = config.get("destination_folder")
    processed_emails_output_folder = os.path.join(os.path.dirname(__file__), "processed_emails_split")  # Folder for split JSON files

    # Ensure folders exist
    os.makedirs(attachment_folder, exist_ok=True)
    os.makedirs(destination_folder, exist_ok=True)
    os.makedirs(processed_emails_output_folder, exist_ok=True)

    db_file = resource_path("DB/db_objects.json")
    logger.info(f"Database file path: {db_file}")
    if not os.path.exists(db_file):
        logger.warning(f"Database file not found: {db_file}")
        return
    
    # Check if max_uid is empty or not set in the config file
    last_uid = get_last_saved_uid()
    if last_uid == 0:  # First execution, initialize the max UID
        logger.info("No max_uid found or UID is 0. Retrieving the last UID from the server...")
        max_uid = get_max_uid_from_server()
        logger.info(f"Max UID from server: (BEF-W) {max_uid}")
        if max_uid > 0:
            save_last_uid(max_uid)
            logger.info(f"Max UID ({max_uid}) saved. No emails will be downloaded on the first run.")
        else:
            logger.warning("Failed to retrieve max UID. Exiting...")
        return  # Exit the program after initializing max_uid to avoid processing emails on the first run

    while True:
        mail = get_imap_connection()

        # Track last processed UID
        last_uid = get_last_saved_uid()

        # Load parameters for processing
        parameters = load_parameters_from_db(db_file)
        if not parameters:
            logger.info("Error: Parameters could not be loaded from the database file.")
            return

        # Download emails and process attachments
        emails = process_emails_since(mail, last_uid)

        if emails:
            processed_emails = []

            processor = AttachmentProcessor(DefaultFileProcessor())

            for email in emails:
                # Process attachments with detailed logic
                updated_email = processor.process_attachments_from_email(
                    email_obj=email,
                    parameters=parameters,  # Use loaded parameters
                    base_destination_folder=destination_folder
                )
                processed_emails.append(updated_email)

            # Save processed emails to JSON
            save_emails_to_json_split(processed_emails, processed_emails_output_folder, max_entries_per_file=1000)

            # Update last_uid
            new_last_uid = max(int(email.uid) for email in emails)
            if new_last_uid > last_uid:
                save_last_uid(new_last_uid)

        mail.logout()
        logger.info("Waiting 5 min before the next run...")
        time.sleep(300)

if __name__ == "__main__":
    main()