import os
from config.loggin_config import logger
from typing import List, Dict
from emails.Email_with_Attachment import EmailWithAttachments
from .strategy import FileProcessorStrategy

class AttachmentProcessor:
    def __init__(self, strategy: FileProcessorStrategy):
        self.strategy = strategy

    def process_attachments_from_email(self, email_obj: EmailWithAttachments, parameters: dict, base_destination_folder: str) -> EmailWithAttachments:
        updated_attachments = []

        for attachment in email_obj.attachments:
            if not os.path.exists(attachment["path"]):
                logger.error(f"Attachment not found: {attachment['path']}")
                updated_attachments.append({
                    "file_name": attachment["file_name"],
                    "path": attachment["path"],
                    "status": "error",
                    "message": "File not found",
                })
                continue

            attachment_info = self.strategy.process(
                file_path=attachment["path"],
                parameters=parameters,
                base_destination_folder=base_destination_folder,
            )
            vendor_name = attachment_info.get("vendor_name") 
            attachment_info["vendor_name"] = vendor_name 

            updated_attachments.append(attachment_info)

        email_obj.attachments = updated_attachments
        return email_obj

    def process_files_in_folder(
            self, folder_path: str, parameters: dict, base_destination_folder: str, vendor_name: str
        ) -> List[dict]:
            """
            Processes all files in a folder using the defined strategy, without restricting by file type.

            Args:
                folder_path (str): Path to the folder containing files to process.
                parameters (dict): Additional parameters for the processing strategy.
                base_destination_folder (str): Base folder where processed files will be stored.
                vendor_name (str): Vendor name to associate with processed files.

            Returns:
                List[dict]: List of results from processing each file.
            """
            results = []
            try:
                if not os.path.exists(folder_path):
                    logger.error(f"Folder does not exist: {folder_path}")
                    return results

                os.makedirs(base_destination_folder, exist_ok=True)
                files = [file_name for file_name in os.listdir(folder_path)]  # No extension filtering

                if not files:
                    logger.info(f"No files found in the folder: {folder_path}")
                    return results

                for file_name in files:
                    file_path = os.path.join(folder_path, file_name)
                    result = self.strategy.process(file_path, parameters, base_destination_folder, vendor_name)
                    results.append(result)

            except Exception as e:
                logger.error(f"An error occurred while processing the folder: {e}")

            return results