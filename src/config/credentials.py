
def input_imap_credentials():
    """
    Prompt the user to input IMAP credentials.

    Returns:
        tuple: IMAP username and password.
    """
    imap_username = input("Enter your email address: ").strip()
    imap_password = input("Enter your password: ").strip()

    if not imap_username or not imap_password:
        raise ValueError("IMAP username and password cannot be empty.")
    
    return imap_username, imap_password

def get_imap_credentials(config):
    """
    Get the IMAP credentials (username and password) from the configuration.

    Args:
        config (dict): The configuration data.

    Returns:
        tuple: The IMAP username and password.
    """
    username = config.get("imap_username")
    password = config.get("imap_password")
    if not username or not password:
        raise ValueError("IMAP username or password is missing in the configuration.")
    return username, password
