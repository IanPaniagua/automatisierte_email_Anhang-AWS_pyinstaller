import os
from config.loggin_config import logger

def create_folder_if_not_exists(path, folder_name):
    """
    Creates a folder at the specified path if it does not already exist.

    Args:
        path (str): The base path where the folder should be created.
        folder_name (str): The name of the folder to create.

    Returns:
        str: The full path of the folder.
    """
    folder_path = os.path.join(path, folder_name)
    os.makedirs(folder_path, exist_ok=True)
    logger.info(f"Folder ensured: {folder_path}")
    return folder_path

def validate_and_create_folder(folder_path):
    """
    Validate if a folder exists, and create it if it doesn't.

    Args:
        folder_path (str): Path to validate or create.

    Returns:
        str: The validated folder path.
    """
    if not os.path.exists(folder_path):
        os.makedirs(folder_path, exist_ok=True)
        logger.info(f"Created folder: {folder_path}")
    else:
        logger.info(f"Using existing folder: {folder_path}")
    return folder_path

def is_valid_folder(folder_path):
    """
    Checks if the given folder path exists and is a directory.

    Args:
        folder_path (str): The folder path to validate.

    Returns:
        bool: True if the folder exists and is a directory, False otherwise.
    """
    return os.path.exists(folder_path) and os.path.isdir(folder_path)