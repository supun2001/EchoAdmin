# import model


# def main():
#     # For testing with hardcoded data
#     body = "Hello, how are you?"
#     reply = model.generate_reply(body)
    
# if __name__ == "__main__":
#     main()

import imaplib
import email
from email.header import decode_header
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
import sys

# Load environment variables from a .env file
load_dotenv()

# --- Configuration ---
# Your .env file in the same directory needs all three keys:
# EMAIL=your-email@gmail.com
# GMAIL_PASSWORD=your-16-character-app-password
# GEMINI_API_KEY=your-gemini-api-key

def fetch_latest_unread_email(username, password):
    """
    Connects to Gmail and fetches the latest unread email.
    Returns (from_address, subject, body) or (None, None, None) on failure.
    """
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(username, password)
        mail.select("inbox")

        # Search for unread emails
        status, messages = mail.search(None, "UNSEEN")
        if status != "OK":
            print("Error searching for unread emails.")
            mail.logout()
            return None, None, None

        email_ids = messages[0].split()
        if not email_ids:
            print("No unread emails found.")
            mail.logout()
            return None, None, None

        # Fetch the latest unread email
        latest_email_id = email_ids[-1]
        status, msg_data = mail.fetch(latest_email_id, "(RFC822)")
        if status != "OK":
            print(f"Error fetching email ID {latest_email_id}")
            mail.logout()
            return None, None, None

        # Parse email content
        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)

        # --- Decode Headers ---
        subject = "No Subject"
        subject_header = msg["Subject"]
        if subject_header:
            subject, encoding = decode_header(subject_header)[0]
            if isinstance(subject, bytes):
                try:
                    subject = subject.decode(encoding or "utf-8")
                except UnicodeDecodeError:
                    subject = subject.decode("latin-1", errors="replace")

        from_ = "No Sender"
        from_header = msg.get("From")
        if from_header:
            from_, encoding = decode_header(from_header)[0]
            if isinstance(from_, bytes):
                try:
                    from_ = from_.decode(encoding or "utf-8")
                except UnicodeDecodeError:
                    from_ = from_.decode("latin-1", errors="replace")

        # --- Extract Body ---
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                if content_type == "text/plain" and "attachment" not in content_disposition:
                    try:
                        charset = part.get_content_charset() or "utf-8"
                        body = part.get_payload(decode=True).decode(charset, errors="replace")
                        break
                    except Exception:
                        continue
        else:
            try:
                charset = msg.get_content_charset() or "utf-8"
                body = msg.get_payload(decode=True).decode(charset, errors="replace")
            except Exception as e:
                print(f"Error decoding non-multipart payload: {e}")
                body = "" # Ensure body is a string

        mail.logout()
        return from_, subject, body

    except imaplib.IMAP4.error as e:
        print(f"IMAP Error: {e}")
        return None, None, None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None, None, None

def generate_reply(body, custom_instruction=None):
    """
    Generates a reply to the email body using the Gemini API.
    Streams the response to the console.
    """
    try:
        # Use the modern GenAI API
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        model = "gemini-2.5-pro"

        base_prompt = (
            "You are an administrative assistant. "
            "Write a single, direct email reply to the message. "
            "Be polite, professional, and helpful. "
            "Be concise, clear, and respectful. "
            "Do not provide multiple options or examples - just write one email response."
        )

        if custom_instruction:
            base_prompt += f"\n\nAdditional instruction: {custom_instruction}"

        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part(text=f"{base_prompt}\n\nMessage:\n{body}")
                ],
            )
        ]
        
        config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_budget=-1),
        )

        response_text = ""
        for chunk in client.models.generate_content_stream(
            model=model, contents=contents, config=config
        ):
            if chunk.text:
                print(chunk.text, end="")
                sys.stdout.flush() # Ensure text prints immediately
                response_text += chunk.text
        
        print() # for newline
        return response_text
    
    except Exception as e:
        print(f"\nError during reply generation: {e}")
        return None

def main():
    # --- Check for all required environment variables ---
    username = os.getenv("EMAIL")
    password = os.getenv("GMAIL_PASSWORD")
    api_key = os.getenv("GEMINI_API_KEY")

    if not username or not password or not api_key:
        print("Error: Missing one or more environment variables.")
        print("Please ensure EMAIL, GMAIL_PASSWORD, and GEMINI_API_KEY are in your .env file.")
        return

    # --- API key is configured in generate_reply function ---

    # --- Step 1: Fetch Email ---
    print("Connecting to Gmail to fetch the latest unread email...")
    from_addr, subject, body = fetch_latest_unread_email(username, password)

    if not body:
        print("Failed to fetch email or no new emails found.")
        return

    # --- Step 2: Show Email and Get Instructions ---
    print("\n--- 📧 Email Received ---")
    print(f"From: {from_addr}")
    print(f"Subject: {subject}")
    print("--- Body (first 500 chars) ---")
    print(body[:500] + "..." if len(body) > 500 else body)
    print("---------------------------\n")

    try:
        custom_instruction = input("Enter any custom reply instruction (or press Enter to skip): ")
    except EOFError:
        custom_instruction = ""
        print()

    # --- Step 3: Generate Reply ---
    print("\n--- 🤖 Generating Reply (powered by Gemini) ---")
    generate_reply(body, custom_instruction or None)
    print("------------------------------------------------")

if __name__ == "__main__":
    main()