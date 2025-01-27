import imaplib
from config.loggin_config import logger
import socket
import time
from config.config import load_config
from config.credentials import get_imap_credentials

# Set a global timeout for all socket connections
socket.setdefaulttimeout(30)

def get_imap_connection(max_retries=5, retry_delay=10):
    """
    Establishes a connection to the IMAP server with retries in case of failure.

    Args:
        max_retries (int): Maximum number of retry attempts before giving up.
        retry_delay (int): Time (in seconds) to wait between retries.

    Returns:
        imaplib.IMAP4_SSL: The IMAP connection object if successful.

    Raises:
        Exception: If all retry attempts fail.
    """
    attempts = 0
    # Load configuration
    config = load_config()

    while attempts < max_retries:
        try:
            # Retrieve credentials
            username, password = get_imap_credentials(config)

            # Ensure credentials are provided
            if not username or not password:
                raise ValueError("IMAP username or password not provided in the configuration.")

            # Connect to the IMAP server
            server = config.get("imap_server", "imap.ionos.es")
            port = config.get("imap_port", 993)
            logger.info(f"Attempt {attempts + 1}/{max_retries}: Connecting to IMAP server {server} on port {port}...")

            # Create the IMAP connection
            mail = imaplib.IMAP4_SSL(server, port)
            mail.login(username, password)

            logger.info(f"Successfully connected to the IMAP server as {username}.")
            return mail  # Return the connection if successful

        except imaplib.IMAP4.error as e:
            # Log authentication errors and retry
            logger.error(f"IMAP login failed: {e}. Retrying in {retry_delay} seconds...")
            attempts += 1
            if attempts >= max_retries:
                raise
            time.sleep(retry_delay)

        except socket.timeout:
            # Log timeout errors and retry
            logger.error(f"Connection attempt timed out. Retrying in {retry_delay} seconds...")
            attempts += 1
            if attempts >= max_retries:
                raise
            time.sleep(retry_delay)

        except Exception as e:
            # Log unexpected errors and retry
            logger.error(f"Unexpected error occurred: {e}. Retrying in {retry_delay} seconds...")
            attempts += 1
            if attempts >= max_retries:
                raise
            time.sleep(retry_delay)

    # If all retries fail, raise a final exception
    logger.error("All connection attempts failed.")
    raise Exception("Unable to establish a connection to the IMAP server after multiple retries.")
