# Invoice Processing with IMAP and AWS Textract

This project connects to an email account via IMAP, downloads attached invoice files, processes them using the AWS Textract API to extract data, renames the files, and moves them to a desired folder. It is currently designed to work on Windows systems.

## Requirements

- Python 3.x
- Required libraries (see installation section)
- IMAP email account (currently works with IONOS)
- AWS Textract configuration
- -Windows


## Initial Configuration

1. **Email IMAP Configuration**: 
   - Open the `config.py` file and provide the following credentials for your email account:
     - `email`: Your email address.
     - `password`: Your email account password.
     - Note: This project is set up to work with IONOS, but you can modify `config.py` if you want to use another provider.

2. **AWS Textract Configuration**:
   - Ensure that your AWS credentials are configured on your local machine. If you haven't configured them, you can do so with the following command:


3. **File Paths**:
   - During execution, you'll be prompted to choose the path where the attachments will be downloaded.
   - After processing, you will also be prompted to choose a path where the files will be moved.

## Usage

1. Run the main script:
   ```bash
   python main.py
   ```

2. The program will start connecting to your inbox, download attachments, and process each invoice with AWS Textract.

3. After processing the files, they will be renamed and moved to the destination folder you selected.

## Features

- Connects to an IMAP server to retrieve emails.
- Downloads attachments (invoices).
- Extracts data from invoices using the AWS Textract API.
- Renames and organizes downloaded files into specific folders.

## Notes

- This project is designed to work on Windows. If you want to use it on other operating systems, some modifications may be necessary.
- The IMAP connection is configured to work with IONOS, but you can adapt it for other email providers by modifying the configuration in `config.py`.
- Make sure not to share your configuration file with sensitive credentials.

