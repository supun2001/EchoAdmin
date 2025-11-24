import imaplib
import email
from email.header import decode_header
import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# --- Configuration ---
# Your .env file in the same directory should look like this:
# EMAIL=your-email@gmail.com
# GMAIL_PASSWORD=your-16-character-app-password

# IMPORTANT: For security, use an "App Password" from Google, not your main password.
# 1. Go to your Google Account settings (myaccount.google.com)
# 2. Go to Security
# 3. Ensure 2-Step Verification is ON
# 4. Under "Signing in to Google," click "App Passwords"
# 5. Generate a new password for "Mail" on "Other (Custom name)" and use that 16-character code.
username = os.getenv("EMAIL")
password = os.getenv("GMAIL_PASSWORD")

if not username or not password:
    print("Error: EMAIL or GMAIL_PASSWORD not found in .env file.")
    print("Please create a .env file with your credentials.")
    exit()

# --- Connect to Gmail ---
try:
    # Connect to Gmail IMAP server
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(username, password)

    # Select the mailbox (inbox)
    mail.select("inbox")

    # Search for all emails (you can change "ALL" to "UNSEEN" to get only unread emails)
    status, messages = mail.search(None, "ALL")

    if status != "OK":
        print("Error searching for emails.")
        mail.logout()
        exit()

    # Get list of email IDs
    email_ids = messages[0].split()

    if not email_ids:
        print("No emails found in the inbox.")
    else:
        # Fetch the latest email
        latest_email_id = email_ids[-1]
        status, msg_data = mail.fetch(latest_email_id, "(RFC822)")

        if status != "OK":
            print(f"Error fetching email ID {latest_email_id}")
            mail.logout()
            exit()

        # Parse email content
        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)

        # --- Decode Email Headers ---
        
        # Decode subject
        subject = "No Subject"
        subject_header = msg["Subject"]
        if subject_header:
            subject, encoding = decode_header(subject_header)[0]
            if isinstance(subject, bytes):
                try:
                    subject = subject.decode(encoding or "utf-8")
                except UnicodeDecodeError:
                    subject = subject.decode("latin-1", errors="replace") # Fallback

        # Decode 'From' address
        from_ = "No Sender"
        from_header = msg.get("From")
        if from_header:
            from_, encoding = decode_header(from_header)[0]
            if isinstance(from_, bytes):
                try:
                    from_ = from_.decode(encoding or "utf-8")
                except UnicodeDecodeError:
                    from_ = from_.decode("latin-1", errors="replace") # Fallback

        print("From:", from_)
        print("Subject:", subject)

        # --- Extract Email Body ---
        body = ""
        if msg.is_multipart():
            # Walk through all parts of the multipart message
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))

                # Look for plain text parts, ignore attachments
                if content_type == "text/plain" and "attachment" not in content_disposition:
                    try:
                        charset = part.get_content_charset() or "utf-8"
                        body = part.get_payload(decode=True).decode(charset, errors="replace")
                        break # Found the plain text body
                    except Exception as e:
                        print(f"Error decoding part: {e}")
        else:
            # Not a multipart message, just get the payload
            try:
                charset = msg.get_content_charset() or "utf-8"
                body = msg.get_payload(decode=True).decode(charset, errors="replace")
            except Exception as e:
                print(f"Error decoding payload: {e}")

        if body:
            print("\nMessage:\n", body)
        else:
            print("\nMessage:\n(Could not find a plain text body)")

    # --- Clean up ---
    mail.logout()

except imaplib.IMAP4.error as e:
    print(f"IMAP Error: {e}")
    print("Failed to login. Check your username, password, and App Password settings.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")