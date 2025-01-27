from config.loggin_config import logger
from .data_loader import load_parameters_from_db
from .processor import AttachmentProcessor
from .strategy import DefaultFileProcessor

def process_attachments(attachment_folder: str, destination_folder: str, db_file: str):
    logger.info("Processing attachments...")
    parameters = load_parameters_from_db(db_file)

    if not parameters:
        logger.error("No parameters loaded. Please check the JSON file.")
        return

    processor = AttachmentProcessor(DefaultFileProcessor())
    results = processor.process_files_in_folder(attachment_folder, parameters, destination_folder)

    for result in results:
        if "file_name" not in result:
            logger.warning(f"Skipping result: Missing 'file_name'. Result: {result}")
            continue

        logger.info(f"\nFile: {result['file_name']}")
        if result.get("eigentümer"):
            logger.info(f"Matched Eigentümer: {result['eigentümer']}")
        if result.get("prefix"):
            logger.info(f"Prefix Applied: {result['prefix']}")
        if result.get("path"):
            logger.info(f"Moved To: {result['path']}")
        else:
            logger.info("No match or relevant keyword found.")