import imaplib
import email
from email.header import decode_header
from email.message import EmailMessage
import email.utils
import smtplib
import os
import time
from dotenv import load_dotenv
from google import genai 
import sys
import requests
from bs4 import BeautifulSoup
import msal 
import json

# Load environment variables from a .env file
load_dotenv()

# --- Configuration ---
# Your .env file in the same directory needs all three keys:
# EMAIL=your-email@outlook.com
# EMAIL_APP_PASSWORD=your-16-character-app-password
# GEMINI_API_KEY=your-gemini-api-key

# How often to check for new emails (in seconds)
CHECK_INTERVAL = 30

# --- !!! NEW AZURE APP CONFIGURATION !!! ---
# You must get these from your App Registration in Microsoft Entra ID (Azure)
# https://learn.microsoft.com/en-us/entra/identity-platform/quickstart-register-app
AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID")
AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
AZURE_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET")
# This is the email address you want the agent to monitor
TARGET_USER_EMAIL = os.getenv("EMAIL") 

MS_GRAPH_ENDPOINT = "https://graph.microsoft.com/v1.0"
MS_GRAPH_SCOPES = ["https://graph.microsoft.com/.default"]


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

# --- MSAL/Graph Authentication ---
def get_graph_token():
    """
    Acquires an OAuth token from Azure for the Graph API
    """
    authority = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}"
    app = msal.ConfidentialClientApplication(
        client_id=AZURE_CLIENT_ID,
        client_credential=AZURE_CLIENT_SECRET,
        authority=authority
    )
    
    result = app.acquire_token_silent(scopes=MS_GRAPH_SCOPES, account=None)
    
    if not result:
        print("No suitable token in cache, acquiring new one...")
        result = app.acquire_token_for_client(scopes=MS_GRAPH_SCOPES)
        
    if "access_token" in result:
        return result["access_token"]
    else:
        print(f"Error acquiring token: {result.get('error_description')}")
        return None

# --- New Function 1: AI Intent Identification (Unchanged) ---
def identify_course_topic(email_body, client, model): 
    # ... (This function is identical to your original)
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
        from google.genai import types
        contents = [
            types.Content(
                role="user",
                parts=[types.Part(text=prompt)]
            )
        ]
        response = client.models.generate_content(model=model, contents=contents)
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


# --- New Function 2: Web Scraper (Unchanged) ---
def scrape_course_info(url):
    # ... (This function is identical to your original)
    print(f"Scraping URL: {url}")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
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

# --- Modified Function 3: AI Reply Generation (Unchanged) ---
def generate_reply(email_body, client, model, context=None, course_name=None): 
    # ... (This function is identical to your original)
    if context:
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
        from google.genai import types
        contents = [
            types.Content(
                role="user",
                parts=[types.Part(text=prompt)]
            )
        ]
        response_text = ""
        print("--- 🤖 Generating Reply ---")
        for chunk in client.models.generate_content_stream(model=model, contents=contents):
            if chunk.text:
                print(chunk.text, end="")
                sys.stdout.flush()
                response_text += chunk.text
        
        print("\n-----------------------------")
        return response_text.strip()
    
    except Exception as e:
        print(f"\nError during reply generation: {e}")
        return None


# --- !!! NEW GRAPH API FUNCTIONS !!! ---

def get_unread_emails_graph(token):
    """
    Fetches unread emails from the inbox using Graph API.
    """
    headers = {'Authorization': f'Bearer {token}'}
    # Get only unread messages, select key fields, get the latest one first
    filter_query = "isRead eq false"
    select_query = "id,subject,from,body"
    orderby_query = "receivedDateTime desc"
    
    url = f"{MS_GRAPH_ENDPOINT}/users/{TARGET_USER_EMAIL}/mailFolders('inbox')/messages"
    params = {
        '$filter': filter_query,
        '$select': select_query,
        '$orderby': orderby_query,
        '$top': 10 # Get top 10, process one by one
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json().get('value', [])
    except Exception as e:
        print(f"Error fetching emails: {e}")
        return []

def send_reply_graph(token, to_email, subject, html_body, original_message_id):
    """
    Sends a reply email using Graph API.
    """
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    
    reply_payload = {
        "message": {
            "toRecipients": [{"emailAddress": {"address": to_email}}],
            "body": {
                "contentType": "HTML",
                "content": html_body
            }
            # Note: When using the /reply endpoint, Graph handles the subject (Re:)
            # and threading (In-Reply-To) automatically.
        },
        "comment": "Replying via automated agent."
    }
    
    # Use the /reply endpoint to keep it in the same thread
    url = f"{MS_GRAPH_ENDPOINT}/users/{TARGET_USER_EMAIL}/messages/{original_message_id}/reply"
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(reply_payload))
        response.raise_for_status() # Will raise error for 4xx/5xx
        print("✅ Reply successfully sent via Graph.")
        return True
    except Exception as e:
        print(f"Error sending reply: {e} - {response.text}")
        return False

def mark_email_as_read_graph(token, message_id):
    """
    Marks an email as read.
    """
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    patch_body = {"isRead": True}
    url = f"{MS_GRAPH_ENDPOINT}/users/{TARGET_USER_EMAIL}/messages/{message_id}"
    
    try:
        response = requests.patch(url, headers=headers, data=json.dumps(patch_body))
        response.raise_for_status()
        print(f"Marked email {message_id} as read.")
    except Exception as e:
        print(f"Error marking as read: {e}")

def flag_email_graph(token, message_id):
    """
    Flags an email for follow-up.
    """
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    patch_body = {"flag": {"flagStatus": "flagged"}}
    url = f"{MS_GRAPH_ENDPOINT}/users/{TARGET_USER_EMAIL}/messages/{message_id}"
    
    try:
        response = requests.patch(url, headers=headers, data=json.dumps(patch_body))
        response.raise_for_status()
        print(f"Flagged email {message_id} for review.")
    except Exception as e:
        print(f"Error flagging email: {e}")


# --- Main Loop (Modified for Graph API) ---
def main():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: Missing GEMINI_API_KEY")
        return
        
    if not AZURE_TENANT_ID or not AZURE_CLIENT_ID or not AZURE_CLIENT_SECRET:
        print("Error: Missing Azure credentials in .env file.")
        print("Please add AZURE_TENANT_ID, AZURE_CLIENT_ID, and AZURE_CLIENT_SECRET")
        return

    try:
        client = genai.Client(api_key=api_key)
        model = "gemini-2.5-pro" 
    except Exception as e:
        print(f"Error configuring Gemini API: {e}")
        return

    print(f"Email agent started for {TARGET_USER_EMAIL}.")
    print(f"Using MS Graph API. Checking every {CHECK_INTERVAL} seconds...")
    print("Press Ctrl+C to stop the agent.")
    
    # --- IMPORTANT ---
    print("This script uses POLLING. For true production, you should use")
    print("Graph Webhooks and an Azure Function to create an event-driven agent.")
    print("-----------------------------------------------------------------")


    while True:
        try:
            token = get_graph_token()
            if not token:
                print("Failed to get Graph token. Retrying...")
                time.sleep(CHECK_INTERVAL)
                continue
                
            unread_emails = get_unread_emails_graph(token)
            
            if not unread_emails:
                print(f"No new emails. Waiting {CHECK_INTERVAL} seconds...")
            else:
                print(f"Found {len(unread_emails)} new email(s). Processing one...")
                # We process the most recent email
                # (Graph already sorted them by receivedDateTime desc)
                email_to_process = unread_emails[0]
                
                msg_id = email_to_process['id']
                subject = email_to_process.get('subject', 'No Subject')
                from_email = email_to_process['from']['emailAddress']['address']
                
                # Graph API gives body in HTML or text, we prefer text for the AI
                body_content = ""
                if email_to_process['body']['contentType'] == 'html':
                    # Simple strip of HTML for AI analysis
                    soup = BeautifulSoup(email_to_process['body']['content'], 'html.parser')
                    body_content = soup.get_text(separator=' ', strip=True)
                else:
                    body_content = email_to_process['body']['content']

                if not body_content or not from_email:
                    print("Could not parse email body. Marking as read.")
                    mark_email_as_read_graph(token, msg_id)
                    continue
                    
                print(f"--- 📧 Email From: {from_email} ---")
                print(f"--- 🧾 Original Subject: {subject} ---")

                # --- LOGIC ---
                # 1. Identify Topic
                course_key = identify_course_topic(body_content, client, model)

                # --- !!! NEW FLAGGING LOGIC !!! ---
                if course_key == 'NONE' or course_key not in COURSE_URLS:
                    print("Identified as 'other inquiry' or unmapped course. Flagging for manual review.")
                    flag_email_graph(token, msg_id)
                    mark_email_as_read_graph(token, msg_id)
                    continue # This skips the reply step
                
                # --- This code now only runs for valid, mapped course inquiries ---
                
                # 2. Scrape if topic found
                context = None
                url = COURSE_URLS[course_key]
                context = scrape_course_info(url)
                if not context:
                    print("Scraping failed, will generate reply for scraping failure.")

                # 3. Generate Reply (with or without context)
                reply_body_html = generate_reply(body_content, model, context, course_name=course_key) 

                if reply_body_html:
                    # 4. Send Reply
                    sent_ok = send_reply_graph(token, from_email, subject, reply_body_html, msg_id)
                    
                    if sent_ok:
                        # 5. Mark as Read
                        mark_email_as_read_graph(token, msg_id)
                else:
                    print("Failed to generate a reply. Email will remain unread.")
            
            # Wait for the next poll
            time.sleep(CHECK_INTERVAL)

        except KeyboardInterrupt:
            print("\nShutting down agent...")
            break
        except Exception as e:
            print(f"An unexpected error occurred in the loop: {e}")
            time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()