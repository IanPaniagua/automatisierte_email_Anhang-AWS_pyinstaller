import logging
import os

# Define the log format
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

# Define the log file path
LOG_FILE = os.path.join("logs", "app.log")

# Ensure the logs directory exists
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

# Configure the logger
logging.basicConfig(
    level=logging.INFO,  # Set the default log level
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler(LOG_FILE),  # Write logs to a file
        logging.StreamHandler()         # Output logs to the console
    ]
)

# Create a logger instance for reuse
logger = logging.getLogger("app_logger")
