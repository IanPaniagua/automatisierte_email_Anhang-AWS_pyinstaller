import os
import json
import logging
from processing.folders.folder_utils import validate_and_create_folder
from config.loggin_config import logger


CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

def load_config(config_file=CONFIG_FILE):
    """
    Load the configuration from a JSON file, or run initial setup if the file does not exist.

    Args:
        config_file (str): Path to the configuration file.

    Returns:
        dict: The configuration data.
    """
    if not os.path.exists(config_file):
        logger.warning(f"Configuration file not found at {config_file}. Running initial setup...")
        return initial_setup(config_file)

    try:
        with open(config_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from {config_file}: {e}")
        raise
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        raise

def save_config(config, config_file=CONFIG_FILE):
    """
    Save configuration data to a JSON file.

    Args:
        config (dict): Configuration data to save.
        config_file (str): Path to the configuration file.
    """
    try:
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
        logger.info(f"Configuration saved to {config_file}")
    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        raise

def initial_setup(config_file=CONFIG_FILE):
    """
    Perform the initial setup to configure the IMAP credentials and attachment folder.

    Args:
        config_file (str): Path to save the configuration file.

    Returns:
        dict: The created configuration data.
    """
    logger.info("Initial setup: Provide the email credentials and attachment folder path.")
    from config.credentials import input_imap_credentials

    imap_username, imap_password = input_imap_credentials()
    attachment_folder = input("Enter the full path for the attachment folder: ").strip()

    # Validate and create folder
    validate_and_create_folder(attachment_folder)

    destination_folder = input("Enter the full path for the processed files folder: ").strip()
    validate_and_create_folder(destination_folder)

    config = {
        "imap_username": imap_username,
        "imap_password": imap_password,
        "attachment_folder": attachment_folder,
        "destination_folder": destination_folder,
    }
    save_config(config, config_file)
    return config
