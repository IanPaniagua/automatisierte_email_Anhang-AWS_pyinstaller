import os
from processing.folders.folder_utils import create_folder_if_not_exists
import shutil
from config.loggin_config import logger
def move_attachment(file_path, destination_folder):
    """
    Moves an attachment to a different folder.

    Args:
        file_path (str): The full path of the attachment to move.
        destination_folder (str): The folder where the attachment will be moved.

    Returns:
        str: The new full path of the moved attachment.
    """
    create_folder_if_not_exists("", destination_folder)
    destination_path = os.path.join(destination_folder, os.path.basename(file_path))
    shutil.move(file_path, destination_path)
    logger.info(f"Attachment moved to: {destination_path}")
    return destination_path

def rename_attachment(file_path, new_name):
    """
    Renames an attachment file.

    Args:
        file_path (str): The full path of the attachment to rename.
        new_name (str): The new name for the attachment.

    Returns:
        str: The new full path of the renamed attachment.
    """
    directory = os.path.dirname(file_path)
    new_path = os.path.join(directory, new_name)
    os.rename(file_path, new_path)
    logger.info(f"Attachment renamed to: {new_path}")
    return new_path

