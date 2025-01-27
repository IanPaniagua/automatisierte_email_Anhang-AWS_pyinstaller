
import os
import boto3
import json
import time
from config.aws_config import get_textract_client
from config.loggin_config import logger
from rapidfuzz import fuzz
import re
from rapidfuzz.process import extractOne
from utils.resource_path import resource_path
from dotenv import load_dotenv

dotenv_path = resource_path('.env')
load_dotenv(dotenv_path) 


S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

def get_s3_client():
    """Get S3 client using the same configuration as textract"""
    session = boto3.Session()
    credentials = session.get_credentials()
    frozen_credentials = credentials.get_frozen_credentials()
    
    return boto3.client(
        's3',
        aws_access_key_id=frozen_credentials.access_key,
        aws_secret_access_key=frozen_credentials.secret_key,
        aws_session_token=frozen_credentials.token
    )
def upload_to_s3(local_file_path, s3_file_name):
    """Upload file to S3 bucket"""
    try:
        s3_client = get_s3_client()
        s3_client.upload_file(local_file_path, S3_BUCKET_NAME, s3_file_name)
        return True
    except Exception as e:
        logger.warning(f"Error uploading to S3: {e}")
        return False

def get_job_results(textract_client, job_id):
    """Get results from completed Textract job"""
    response = textract_client.get_expense_analysis(JobId=job_id)
    return response

def analyze_document_pages(file_path, output_json_path):
    textract_client = get_textract_client()
    s3_client = get_s3_client()
    
    try:
        if file_path.lower().endswith((".pdf", ".jpeg", ".png")):
            # Upload to S3
            s3_file_name = os.path.basename(file_path)
            if not upload_to_s3(file_path, s3_file_name):
                return

            # Start async analysis
            response = textract_client.start_expense_analysis(
                DocumentLocation={
                    'S3Object': {
                        'Bucket': S3_BUCKET_NAME,
                        'Name': s3_file_name
                    }
                }
            )
            
            job_id = response['JobId']
            logger.info(f" Started analysis job: {job_id}")

            # Wait for job completion with a timeout
            max_retries = 10  # Maximum number of retries
            retries = 0

            # Wait for job completion
            while True:
                response = textract_client.get_expense_analysis(JobId=job_id)
                status = response['JobStatus']
                logger.info(f"Status: {status}")
                
                if status in ['SUCCEEDED', 'FAILED']:
                    break

                if retries >= max_retries:
                    logger.warning("Timeout reached: Job is still in progress.")
                    return               
                retries += 1
                time.sleep(5)

            if status == 'FAILED':
                logger.error("Analysis job failed")
                return

            # Get results
            response = get_job_results(textract_client, job_id)

            # Save response to JSON
            with open(output_json_path, "w", encoding="utf-8") as json_file:
                json.dump(response, json_file, indent=4, ensure_ascii=False)

            logger.info(f"\nFull response saved to {output_json_path}\n")

            # Delete the file from S3 after processing
            delete_from_s3(s3_file_name)

        else:
            logger.warning("The file is not in a supported format. Supported formats: PDF, JPG, PNG")

    except Exception as e:
        logger.error(f" Error processing the file: {e}")

def extract_field_with_max_confidence(response, search_keywords):
    """
    Extracts the field with the highest confidence based on a list of search keywords.
    
    :param response: The Textract response containing invoice data.
    :param search_keywords: A list of keywords to search for in the fields.
    :return: The field value with the highest confidence, and its confidence score.
    """
    max_confidence = 0.0
    max_value = None
    field_type = None
    
    for expense_doc in response.get("ExpenseDocuments", []):
        for field in expense_doc.get("SummaryFields", []):
            field_name = field.get("Type", {}).get("Text", "Unknown")
            label_name = field.get("LabelDetection", {}).get("Text", "Unknown")
            if any(keyword.lower() in field_name.lower() for keyword in search_keywords) or any(keyword.lower() in label_name.lower() for keyword in search_keywords):
                value = field.get("ValueDetection", {}).get("Text", "Unknown")
                confidence = field.get("ValueDetection", {}).get("Confidence", 0.0)

                if confidence > max_confidence:
                    max_confidence = confidence
                    max_value = value
                    field_type = field_name

    return max_value, max_confidence, field_type


def extract_invoice_number_from_response(response):
    """
    Extracts the invoice number from Textract Expense analysis response using fuzzy matching.
    
    :param response: The Textract response containing invoice data.
    :return: Tuple of (invoice_number, confidence) or (None, None) if not found.
    """
    # Base patterns to match against
    invoice_patterns = [
        "rechnung nr",
        "rechnungsnummer",
        "invoice number",
        "invoice no",
        "rechnung",
        "Rechnung",
        "Rechnung Nr.",
        "Rechnungs Nr.",
        "Belegnummer",
    ]
    
    # Minimum similarity score to consider a match (0-100)
    SIMILARITY_THRESHOLD = 80

    # Minimum confidence for detected values
    CONFIDENCE_THRESHOLD = 80.0

    # Excluded labels to avoid confusion
    excluded_labels = ["kdnr", "kundennummer", "Kunden-Nr.:", "steuer id", "steuer-id nr", "tax id"]

    # Regular expression for valid invoice numbers
    invoice_regex = re.compile(r"^[\w\-\/]{5,}$")   # Alphanumeric strings with at least 5 characters, including hyphens

    # Regular expression to remove unwanted prefixes like "Invoice Number:"
    unwanted_prefix_regex = re.compile(r"^(invoice number:|rechnung nr:|rechnungsnummer:|invoice no:|rechnung:|rechnung nr|rechnungs nr:)?\s*")

    for expense_doc in response.get("ExpenseDocuments", []):
        for field in expense_doc.get("SummaryFields", []):
            field_type = field.get("Type", {}).get("Text", "").lower()
            label = field.get("LabelDetection", {}).get("Text", "").lower()
            
            # Check if field_type explicitly indicates an invoice number
            if field_type == "invoice_receipt_id" or any(pattern in label for pattern in invoice_patterns):
                value = field.get("ValueDetection", {}).get("Text", "")
                confidence = field.get("ValueDetection", {}).get("Confidence", 0.0)

                # Clean the value by removing unwanted prefixes
                value = unwanted_prefix_regex.sub("", value)

                if confidence >= CONFIDENCE_THRESHOLD:
                    # Skip if the value is too short (5 digits or less)
                    if len(value) <= 5:
                        continue

                    # Validate invoice number format
                    if invoice_regex.match(value):
                        return value, confidence

            # Skip excluded labels
            if any(excluded_label in label for excluded_label in excluded_labels):
                continue
            
            # Fuzzy match against invoice-related patterns in the label
            match = extractOne(
                label,
                invoice_patterns,
                scorer=fuzz.WRatio,  # Weighted ratio for better matching
                score_cutoff=SIMILARITY_THRESHOLD
            )
            
            if match:
                value = field.get("ValueDetection", {}).get("Text", "")
                confidence = field.get("ValueDetection", {}).get("Confidence", 0.0)

                # Clean the value by removing unwanted prefixes
                value = unwanted_prefix_regex.sub("", value)

                # Skip if the value is too short (5 digits or less)
                if len(value) <= 5:
                    continue

                # Additional validation: Ensure value matches the invoice number format
                if invoice_regex.match(value) and confidence >= CONFIDENCE_THRESHOLD:
                    return value, confidence

    return None, None




def extract_vendor_name_from_response(response):
    """
    Extracts the vendor name with the highest confidence from the Textract response.
    
    :param response: The Textract response containing invoice data.
    :return: The vendor name with the highest confidence and its confidence (None if not found).
    """
    vendor_name, confidence, _ = extract_field_with_max_confidence(response, ["vendor_name"])
    return vendor_name, confidence

def extract_text_from_response(response):
    """
    Extracts all text from the Textract response and returns it as a single string.
    
    :param response: The Textract response containing invoice data.
    :return: A string containing all the extracted text.
    """
    text = []

    # Extract text from SummaryFields (fields like Invoice Number, Date, Vendor Name, etc.)
    for expense_doc in response.get("ExpenseDocuments", []):
        for field in expense_doc.get("SummaryFields", []):
            value = field.get("ValueDetection", {}).get("Text", "").strip()
            if value:
                text.append(value)

    # Extract text from LineItemGroups (detailed line items in invoices)
    for expense_doc in response.get("ExpenseDocuments", []):
        for group in expense_doc.get("LineItemGroups", []):
            for item in group.get("LineItems", []):
                for field in item.get("LineItemExpenseFields", []):
                    value = field.get("ValueDetection", {}).get("Text", "").strip()
                    if value:
                        text.append(value)
    # Extract text from LINE blocks (general text like addresses and names)
    for block in response.get("Blocks", []):
        if block.get("BlockType") == "LINE":
            line_text = block.get("Text", "").strip()
            if line_text:
                text.append(line_text)
    return "\n".join(text)

def extract_document_type_from_response(response):
    """
    Extracts the document type from Textract response based on fuzzy matching for 'Rechnung' (invoice) or 'Lieferschein' (delivery note).
    
    :param response: The Textract response containing invoice data.
    :return: A tuple with the document type ('Rechnung' or 'Lieferschein') and its confidence score.
    """
    # Keywords to identify the document type
    rechnung_keywords = ["rechnung", "rechnungsnummer", "invoice", "rechnung nr", "rechnungs nr"]
    lieferschein_keywords = ["lieferschein", "lieferung", "delivery", "shipping", "lieferschein nr", "lieferung nr"]

    # Minimum confidence threshold for fuzzy matching
    CONFIDENCE_THRESHOLD = 80.0
    
    # Regular expression to clean the document content
    unwanted_prefix_regex = re.compile(r"^(invoice number:|rechnung nr:|rechnungsnummer:|invoice no:|rechnung:|rechnung nr|rechnungs nr:)?\s*")
    
    # Iterate over the fields in the Textract response
    for expense_doc in response.get("ExpenseDocuments", []):
        for field in expense_doc.get("SummaryFields", []):
            field_type = field.get("Type", {}).get("Text", "").lower()
            label = field.get("LabelDetection", {}).get("Text", "").lower()

            # Fuzzy match against 'Rechnung' and 'Lieferschein' keywords
            match_rechnung = extractOne(
                label,
                rechnung_keywords,
                scorer=fuzz.WRatio,  # Weighted ratio for better matching
                score_cutoff=CONFIDENCE_THRESHOLD
            )
            
            match_lieferschein = extractOne(
                label,
                lieferschein_keywords,
                scorer=fuzz.WRatio,  # Weighted ratio for better matching
                score_cutoff=CONFIDENCE_THRESHOLD
            )
            
            # If we find a strong match for either document type, return it
            if match_rechnung:
                return "Rechnung", match_rechnung[1]
            elif match_lieferschein:
                return "Lieferschein", match_lieferschein[1]
    
    return None, None

def delete_from_s3(s3_file_name):
    """Delete file from S3 bucket"""
    try:
        s3_client = get_s3_client()
        s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=s3_file_name)
        logger.info(f"Deleted {s3_file_name} from S3.")
    except Exception as e:
        logger.warning(f"Error deleting {s3_file_name} from S3: {e}")

