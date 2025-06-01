import os.path
import base64
import re
from bs4 import BeautifulSoup
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Gmail read-only scope
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def authenticate_gmail():
    creds = None
    token_path = 'config/token.json'
    creds_path = 'config/credentials.json'

    # Load saved credentials
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    else:
        flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
        creds = flow.run_local_server(port=0)
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
    
    return build('gmail', 'v1', credentials=creds)

def get_recent_job_emails(service, max_results=5):
    query = 'from:(jobs-noreply@linkedin.com) subject:(Job Alert)'
    results = service.users().messages().list(userId='me', q=query, maxResults=max_results).execute()
    messages = results.get('messages', [])
    return messages

def extract_links_from_email(service, msg_id):
    msg = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
    payload = msg['payload']
    
    parts = payload.get('parts', [])
    data = None

    # Look for the HTML part
    for part in parts:
        if part.get('mimeType') == 'text/html':
            data = part['body']['data']
            break

    if not data:
        return []

    html = base64.urlsafe_b64decode(data.encode('UTF-8')).decode('utf-8')
    soup = BeautifulSoup(html, 'html.parser')
    links = [a['href'] for a in soup.find_all('a', href=True) if 'linkedin.com/jobs' in a['href']]
    return list(set(links))  # remove duplicates

def fetch_linkedin_job_links():
    service = authenticate_gmail()
    messages = get_recent_job_emails(service)

    all_links = []
    for msg in messages:
        links = extract_links_from_email(service, msg['id'])
        all_links.extend(links)
    
    return list(set(all_links))  # Deduplicate

if __name__ == "__main__":
    job_links = fetch_linkedin_job_links()
    print(f"Found {len(job_links)} job postings:")
    for link in job_links:
        print(link)
