import imaplib
import email
from email.header import decode_header
from email.message import EmailMessage
import email.utils
import smtplib
import os
import time
from dotenv import load_dotenv
import google.generativeai as genai 
import sys
import requests
from bs4 import BeautifulSoup

# Load environment variables from a .env file
load_dotenv()

# --- Configuration ---
# Your .env file in the same directory needs all three keys:
# EMAIL=your-email@outlook.com
# EMAIL_APP_PASSWORD=your-16-character-app-password
# GEMINI_API_KEY=your-gemini-api-key

# How often to check for new emails (in seconds)
CHECK_INTERVAL = 30

# --- Outlook Server Configuration ---
# Use the servers for personal @outlook.com, @hotmail.com
OUTLOOK_IMAP_SERVER = "imap-mail.outlook.com"
OUTLOOK_SMTP_SERVER = "smtp.office365.com" # This one is often the same
OUTLOOK_SMTP_PORT = 587


# --- !!! IMPORTANT: SET UP YOUR COURSES HERE !!! ---
COURSE_URLS = {
    # Simple, lowercase keys are MUCH easier for the AI to match
    "crowd management": "https://www.glasgowmaritimeacademy.com/crowd-management-cm/",
    "crowd_management_(CM)": "https://www.glasgowmaritimeacademy.com/crowd-management-cm/",
    "cm": "https://www.glasgowmaritimeacademy.com/crowd-management-cm/",
    "marine boilers": "https://www.glasgowmaritimeacademy.com/course/marine-boilers-course/",
    "marine_boilers_course": "https://www.glasgowmaritimeacademy.com/course/marine-boilers-course/",
    "bridge resource management": "https://www.glasgowmaritimeacademy.com/bridge-resource-management-brm/",
    "bridge_resource_management_(BRM)": "https://www.glasgowmaritimeacademy.com/bridge-resource-management-brm/",
    "brm": "https://www.glasgowmaritimeacademy.com/bridge-resource-management-brm/",
    "ecdis training": "https://www.glasgowmaritimeacademy.com/manufacturer-approved-type-specific-ecdis-training/",
    "manufacturer approved type specific ecdis training": "https://www.glasgowmaritimeacademy.com/manufacturer-approved-type-specific-ecdis-training/",
    "manufacturer_approved_TYPE_specific_ecdis_training": "https://www.glasgowmaritimeacademy.com/manufacturer-approved-type-specific-ecdis-training/",
    # Add all your other courses here...
}

# --- New Function 1: AI Intent Identification ---
def identify_course_topic(email_body, model): 
    """
    Uses AI to classify the email and identify which course it's about.
    Returns one of the keys from COURSE_URLS or 'NONE'.
    """
    course_keys = list(COURSE_URLS.keys())
    
    prompt = (
        "You are a text classifier. Read the email below and identify which single course "
        f"it is about. Your entire response must be ONLY ONE of the following keys:\n"
        f"{course_keys}\n"
        "If the email is not about any of these specific courses, or is a general inquiry, "
        "respond with ONLY the word: NONE\n\n"
        "Email:\n"
        f"{email_body}"
    )
    
    try:
        response = model.generate_content(prompt)
        # Clean up the AI's response to get just the key
        topic = response.text.strip().lower().replace("'", "").replace('"', '')
        
        if topic in course_keys:
            print(f"AI identified topic: {topic}")
            return topic
        else:
            print("AI identified topic: NONE (General inquiry)")
            return 'NONE'
    except Exception as e:
        print(f"Error during AI topic identification: {e}")
        return 'NONE'

# --- New Function 2: Web Scraper ---
def scrape_course_info(url):
    """
    Visits a URL, scrapes its content, and returns clean text.
    """
    print(f"Scraping URL: {url}")
    try:
        headers = {
            'User-Agent': 'Mozilla.org/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status() 

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Generic fallback:
        content_area = soup.body

        if content_area:
            text = content_area.get_text(separator=' ', strip=True)
            clean_text = ' '.join(text.split())
            return clean_text[:4000] # Limit context size
        else:
            print("Could not find content area in page.")
            return None

    except requests.RequestException as e:
        print(f"Error scraping URL {url}: {e}")
        return None

# --- Modified Function 3: AI Reply Generation ---
def generate_reply(email_body, model, context=None, course_name=None): 
    """
    Generates a reply to the email body using the Gemini API.
    Uses 'context' (scraped data) if provided.
    """
    
    # --- !!! PROMPT IS NOW FIXED TO REQUEST HTML !!! ---
    if context:
        # We have scraped data! Use it to answer.
        prompt = (
            "You are an administrative assistant for the Glasgow Maritime Academy. "
            "A user sent the following email. Answer their questions *using only* the "
            "scraped 'Course Information' provided below. "
            "Write ONLY the body of the email reply in simple HTML. "
            "Do NOT write a subject line. Do NOT use bullet points (* or <ul>). "
            "Instead, make key points bold using <b>...</b> tags and use <br> for line breaks. "
            "Do NOT include any preamble like 'Of course, here is the reply'. "
            "Start your response directly with the greeting (e.g., '<p>Dear [Name],</p>').\n\n"
            "--- User Email ---\n"
            f"{email_body}\n\n"
            "--- Course Information ---\n"
            f"{context}\n\n"
            "--- Your HTML Reply Body ---\n"
        )
    else:
        # --- THIS IS THE NEW "SCRAPING FAILED" PROMPT ---
        # This block now runs only if we identified a course but scraping failed.
        prompt = (
            "You are an administrative assistant for the Glasgow Maritime Academy. "
            f"A user sent the following email about the course: '{course_name}'. "
            "You were unable to automatically retrieve the course details from the website (scraping failed). "
            "Write a polite, professional HTML reply. "
            "Apologize that you couldn't fetch the details right now, but confirm you will look into it. "
            "Direct them to the main website (www.glasgowmaritimeacademy.com) as a backup. "
            "Write ONLY the body of the email reply in simple HTML. "
            "Do NOT write a subject line. Use <p> tags for paragraphs. "
            "Start your response directly with the greeting (e.g., '<p>Dear [Name],</p>').\n\n"
            "--- User Email ---\n"
            f"{email_body}\n\n"
            "--- Your HTML Reply Body ---\n"
        )

    try:
        response_text = ""
        print("--- 🤖 Generating Reply ---")
        response = model.generate_content(prompt, stream=True)
        
        for chunk in response:
            if chunk.text:
                print(chunk.text, end="")
                sys.stdout.flush()
                response_text += chunk.text
        
        print("\n-----------------------------")
        # Clean up any leading/trailing whitespace just in case
        return response_text.strip()
    
    except Exception as e:
        print(f"\nError during reply generation: {e}")
        return None

# --- !!! FUNCTION MODIFIED TO SEND HTML WITH OUTLOOK !!! ---
def send_reply(username, password, from_addr, to_addr, subject, html_body):
    """
    Sends a multipart/alternative email with both HTML and plain-text fallbacks.
    Uses Outlook SMTP servers with STARTTLS.
    """
    try:
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['To'] = to_addr
        msg['From'] = from_addr
        
        # Create a plain-text version from the HTML
        try:
            soup = BeautifulSoup(html_body, 'html.parser')
            plain_text_body = soup.get_text(separator='\n')
        except Exception:
            plain_text_body = "Could not load message. Please enable HTML emails."

        # Set the plain-text version as the main content
        msg.set_content(plain_text_body)
        
        # Add the HTML version as an 'alternative'
        msg.add_alternative(html_body, subtype='html')
        
        # --- Outlook SMTP (STARTTLS) Logic ---
        with smtplib.SMTP(OUTLOOK_SMTP_SERVER, OUTLOOK_SMTP_PORT) as server:
            server.starttls() # Secure the connection
            server.login(username, password)
            server.send_message(msg)
        # --- End Outlook Logic ---

        print("✅ Reply successfully sent (HTML + Plain Text).")
        return True
    except smtplib.SMTPException as e:
        print(f"Error: Unable to send email. {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred during sending: {e}")
        return False

# --- Fixed Function: parse_email ---
def parse_email(raw_email):
    msg = email.message_from_bytes(raw_email)
    
    subject = "No Subject" # Default value
    subject_header = msg.get("Subject") # Use .get() for safety
    
    if subject_header:
        try:
            subject, encoding = decode_header(subject_header)[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding or "utf-8", errors="replace")
        except Exception as e:
            print(f"Warning: Could not decode subject header. Error: {e}")
            subject = "No Subject" # Fallback

    from_header = msg.get("From")
    from_tuple = email.utils.parseaddr(from_header) # ("Full Name", "email@add.com")
    from_full = from_tuple[0] or from_tuple[1] # Use name, or email if name is blank
    from_email = from_tuple[1] # Just the email

    if isinstance(from_full, bytes):
        try:
            from_full = from_full.decode("utf-8", errors="replace")
        except Exception:
            from_full = from_tuple[1] # Fallback to just email if name is weird

    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            cdispo = str(part.get("Content-Disposition"))
            if ctype == "text/plain" and "attachment" not in cdispo:
                try:
                    charset = part.get_content_charset() or "utf-8"
                    body = part.get_payload(decode=True).decode(charset, errors="replace")
                    break
                except Exception: continue
    else:
        try:
            charset = msg.get_content_charset() or "utf-8"
            body = msg.get_payload(decode=True).decode(charset, errors="replace")
        except Exception: body = ""
    return from_full, from_email, subject, body

# --- Main Loop (Modified for Outlook and Flagging) ---
def main():
    username = os.getenv("EMAIL")
    # --- Renamed variable ---
    password = os.getenv("EMAIL_APP_PASSWORD")
    api_key = os.getenv("GEMINI_API_KEY")

    if not username or not password or not api_key:
        print("Error: Missing one or more environment variables.")
        print("Please check your .env file for EMAIL, EMAIL_APP_PASSWORD, and GEMINI_API_KEY")
        return

    try:
        # Configure the modern library
        genai.configure(api_key=api_key)
        # Create a single model instance to reuse
        model = genai.GenerativeModel("gemini-2.5-pro") 
    except Exception as e:
        print(f"Error configuring Gemini API: {e}")
        return

    print(f"Email agent started for {username}.")
    print(f"Connecting to {OUTLOOK_IMAP_SERVER}...")
    print(f"Checking for new unread emails every {CHECK_INTERVAL} seconds...")
    print("Press Ctrl+C to stop the agent.")

    mail = None
    try:
        # --- Use Outlook IMAP Server ---
        mail = imaplib.IMAP4_SSL(OUTLOOK_IMAP_SERVER)
        mail.login(username, password)
        
        while True:
            try:
                mail.select("inbox")
                status, messages = mail.search(None, "UNSEEN")
                
                if status != "OK":
                    print("Error searching. Reconnecting...")
                    raise imaplib.IMAP4.error("Search failed")

                email_ids = messages[0].split()
                if not email_ids:
                    print(f"No new emails. Waiting {CHECK_INTERVAL} seconds...")
                else:
                    latest_email_id = email_ids[-1]
                    print(f"\nFound new email (ID: {latest_email_id.decode()}). Fetching...")
                    status, msg_data = mail.fetch(latest_email_id, "(RFC822)")
                    
                    if status == "OK":
                        raw_email = msg_data[0][1]
                        from_full, from_email, subject, body = parse_email(raw_email)

                        if not body or not from_email:
                            print("Could not parse email. Skipping.")
                            mail.store(latest_email_id, '+FLAGS', '\\Seen')
                            continue

                        print(f"--- 📧 Email From: {from_full} <{from_email}> ---")
                        print(f"--- 🧾 Original Subject: {subject} ---")

                        # --- LOGIC ---
                        # 1. Identify Topic
                        course_key = identify_course_topic(body, model)

                        # --- !!! NEW FLAGGING LOGIC !!! ---
                        # If the AI determines this is not a course email,
                        # flag it for manual review and mark as read.
                        if course_key == 'NONE' or course_key not in COURSE_URLS:
                            print("Identified as 'other inquiry' or unmapped course. Flagging for manual review.")
                            # Flag the email in the inbox
                            mail.store(latest_email_id, '+FLAGS', '\\Flagged')
                            # Also mark it as read so we don't process it again
                            mail.store(latest_email_id, '+FLAGS', '\\Seen')
                            continue # This skips the reply step
                        
                        # --- This code now only runs for valid, mapped course inquiries ---
                        
                        # 2. Scrape if topic found
                        context = None
                        url = COURSE_URLS[course_key]
                        context = scrape_course_info(url)
                        if not context:
                            print("Scraping failed, will generate reply for scraping failure.")

                        # 3. Generate Reply (with or without context)
                        reply_body = generate_reply(body, model, context, course_name=course_key) # This is now HTML

                        if reply_body:
                            # 4. Send Reply
                            reply_subject = f"Re: {subject}"
                            # send_reply now handles the HTML body
                            sent_ok = send_reply(username, password, username, from_email, reply_subject, reply_body)
                            
                            if sent_ok:
                                # 5. Mark as Read
                                mail.store(latest_email_id, '+FLAGS', '\\Seen')
                                print(f"Marked email {latest_email_id.decode()} as read.")
                        else:
                            print("Failed to generate a reply. Email will remain unread.")
                    
                time.sleep(CHECK_INTERVAL)

            except imaplib.IMAP4.error as e:
                print(f"IMAP Error: {e}. Reconnecting...")
                time.sleep(10)
                try:
                    if mail: mail.logout()
                except: pass
                # --- Use Outlook IMAP Server for reconnection ---
                mail = imaplib.IMAP4_SSL(OUTLOOK_IMAP_SERVER)
                mail.login(username, password)
            except Exception as e:
                print(f"An unexpected error occurred in the loop: {e}")
                time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        print("\nShutting down agent...")
    except imaplib.IMAP4.error as e:
        print(f"IMAP Login Error: {e} (Check credentials and App Password)")
    finally:
        if mail:
            try:
                if mail.state in ('SELECTED', 'AUTH'):
                    mail.close()
                mail.logout()
                print(f"Logged out from {OUTLOOK_IMAP_SERVER}.")
            except Exception as e:
                print(f"Error during logout: {e}")

if __name__ == "__main__":
    main()