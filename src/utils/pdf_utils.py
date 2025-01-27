
import re
import unicodedata
from config.loggin_config import logger

def clean_and_normalize_text(text):
    """
    Cleans and normalizes the extracted text to remove noise and improve structure.

    Args:
        text (str): The raw text extracted from the PDF.

    Returns:
        str: The cleaned and normalized text.
    """
    text = unicodedata.normalize('NFKD', text)  # Normalize Unicode characters
    text = text.replace("\n", " ")  # Replace line breaks with spaces
    text = text.replace(",", ".")  # Normalize decimal separators
    text = re.sub(r"\s+", " ", text)  # Replace multiple spaces with a single space
    text = re.sub(r"[^\w\s.,:;-]", "", text)  # Remove unwanted special characters
    return text.strip()