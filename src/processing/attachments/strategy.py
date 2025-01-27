import os
from config.loggin_config import logger
from utils.pdf_utils import clean_and_normalize_text
from processing.attachments.data_handler import fuzzy_match
from processing.file_handler import rename_attachment, move_attachment
from AWS_TEXTRACT.analyze_expense import analyze_document_pages, extract_text_from_response, extract_document_type_from_response, extract_invoice_number_from_response, extract_vendor_name_from_response
from utils.resource_path import resource_path
import json

class FileProcessorStrategy:
    def process(self, file_path: str, parameters: dict, base_destination_folder: str, threshold: int = 60) -> dict:
        raise NotImplementedError

class DefaultFileProcessor(FileProcessorStrategy):
    def process(self, file_path: str, parameters: dict, base_destination_folder: str,  threshold: int = 60) -> dict:
        file_name = None
        try:
            logger.info(f"Processing file: {file_path}")
            output_json_path = resource_path("output_response.json")

            if not os.path.exists(output_json_path):
                logger.warning(f"Output JSON file does not exist. Creating a new one: {output_json_path}")
                with open(output_json_path, "w", encoding="utf-8") as file:
                    json.dump({}, file)           

            analyze_document_pages(file_path, output_json_path)
            
            with open(output_json_path, "r", encoding="utf-8") as file:
                response = json.load(file)

          # Extract data from AWS
            invoice_number, inv_confidence = extract_invoice_number_from_response(response)
            vendor_name, ven_confidence = extract_vendor_name_from_response(response)
            doc_type, doc_confidence = extract_document_type_from_response(response)

            # Extract text from 
            text_from_JSON = extract_text_from_response(response)

            normalized_text = clean_and_normalize_text(text_from_JSON)
            
            print(f"Document type: {doc_type}")
            if doc_type == "Rechnung":
                prefix = "RG_"
            elif doc_type == "Lieferchein":
                prefix = "LI_"
            else:
                prefix = None
            
            file_name = os.path.basename(file_path)
            file_extension = os.path.splitext(file_name)[1] 

            matched_entry = None
            for entry in parameters:
                eigentümer = clean_and_normalize_text(entry.get("eigentümer", ""))
                if fuzzy_match(normalized_text, eigentümer, threshold):
                    matched_entry = entry
                    break

            verw_nr = matched_entry["verw_nr"] if matched_entry else None
            sanitized_invoice_number = invoice_number.replace("/", "_") if invoice_number else None
            sanitized_vendor_name = vendor_name.replace("/", "_") if vendor_name else None
            new_name_parts = [
                verw_nr, 
                prefix.rstrip("_") if prefix else None,
                sanitized_vendor_name,
                sanitized_invoice_number
            ]

            new_name = "_".join(filter(None, new_name_parts)) + file_extension
            renamed_path = rename_attachment(file_path, new_name)

            os.makedirs(base_destination_folder, exist_ok=True)
            moved_path = move_attachment(renamed_path, base_destination_folder)

            return {
                "file_name": file_name,
                "path": moved_path,
                "invoice_number": invoice_number,
                "vendor_name": vendor_name,
                "doc_type": doc_type,
                "status": "processed" if matched_entry or prefix else "manual_review",
                "verw_nr": matched_entry["verw_nr"] if matched_entry else None,
                "eigentümer": matched_entry["eigentümer"] if matched_entry else "Unknown",
            }

        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            return {
                "file_name": file_name,
                "path": file_path,
                "invoice_number": None,
                "vendor_name": None,
                "doc_type": "UNKNOWN",
                "status": "error",
            }
