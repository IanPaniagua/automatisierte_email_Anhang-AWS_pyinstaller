import sys
import os

def resource_path(relative_path):
    """
    Get the absolute path to a resource, accounting for both packaged and development environments.

    Args:
        relative_path (str): The relative path to the file or resource.

    Returns:
        str: The absolute path to the resource.
    """
    try:
        # Temporary folder used by PyInstaller
        base_path = sys._MEIPASS
    except AttributeError:
        # Add "src/" in development mode
        base_path = os.path.abspath(os.path.join(".", "src"))
    return os.path.join(base_path, relative_path)
