import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
from datetime import datetime
import pytz
import re

# Scopes to access Google Drive
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

# Authenticate and create service
def authenticate_drive():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('secrets/my_secret.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    service = build('drive', 'v3', credentials=creds)
    return service

# Function to sanitize file and folder names (remove/replace invalid characters and trim spaces)
def sanitize_filename(filename):
    sanitized_name = re.sub(r'[<>:"/\\|?*]', '_', filename).strip()
    return sanitized_name

# Function to download a file (including handling Google Docs export)
def download_file(service, file_id, file_name, mime_type, folder_path):
    sanitized_file_name = sanitize_filename(file_name)
    print(f"Downloading file name: {file_name}")
    print(f"mime_type: {mime_type}")
    print(f"folder_path: {folder_path}")

    # Sanitize folder path and create directories if they don't exist
    file_path = os.path.join(folder_path, sanitized_file_name)
    os.makedirs(folder_path, exist_ok=True)

    # Handle different MIME types
    if mime_type == 'application/vnd.google-apps.document':
        request = service.files().export_media(fileId=file_id, mimeType='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        file_path = file_path if file_path.endswith('.docx') else file_path + '.docx'
    elif mime_type == 'application/vnd.google-apps.spreadsheet':
        request = service.files().export_media(fileId=file_id, mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        file_path = file_path if file_path.endswith('.xlsx') else file_path + '.xlsx'
    elif mime_type == 'application/vnd.google-apps.presentation':
        request = service.files().export_media(fileId=file_id, mimeType='application/vnd.openxmlformats-officedocument.presentationml.presentation')
        file_path = file_path if file_path.endswith('.pptx') else file_path + '.pptx'
    else:
        request = service.files().get_media(fileId=file_id)

    try:
        # Download the file
        with io.FileIO(file_path, 'wb') as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                print(f"Downloading {sanitized_file_name} {int(status.progress() * 100)}%.")
    except Exception as e:
        error_message = str(e)
        if 'This file is too large to be exported.' in error_message:
            print(f"Can't download {sanitized_file_name}, file too large. Skipping file...")
        else:
            print(f"Unexpected Error: {error_message}")

# Check if local file exists and if it's up to date
def is_file_up_to_date(file_path, remote_modified_time):
    if os.path.exists(file_path):
        local_modified_time = datetime.utcfromtimestamp(os.path.getmtime(file_path)).replace(tzinfo=pytz.UTC)
        remote_modified_time = datetime.strptime(remote_modified_time, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=pytz.UTC)
        return local_modified_time >= remote_modified_time
    return False

# Recursive function to download all files and process subfolders
def download_files_recursively(service, drive_id, folder_id, parent_path):
    print(f"Fetching files for folder ID: {folder_id} in drive ID: {drive_id}")

    query = f"'{folder_id}' in parents and trashed=false"
    results = service.files().list(q=query, corpora='drive', driveId=drive_id, includeItemsFromAllDrives=True,
                                   supportsAllDrives=True,
                                   fields="nextPageToken, files(id, name, mimeType, modifiedTime)").execute()
    items = results.get('files', [])

    for item in items:
        file_name = item['name']
        mime_type = item['mimeType']
        file_id = item['id']
        modified_time = item['modifiedTime']

        # Skip unsupported media types
        if mime_type not in ['application/vnd.google-apps.document',
                             'application/vnd.google-apps.spreadsheet',
                             'application/vnd.google-apps.presentation',
                             'application/pdf',
                             'application/json',
                             'application/vnd.google-apps.folder']:
            print(f"Skipping mime type: {mime_type} for {file_name}")
            continue

        # Handle folders and files
        if mime_type == 'application/vnd.google-apps.folder':
            # Sanitize folder name
            folder_path = os.path.join(parent_path, sanitize_filename(file_name))
            download_files_recursively(service, drive_id, file_id, folder_path)
        else:
            file_path = os.path.join(parent_path, sanitize_filename(file_name))
            if is_file_up_to_date(file_path, modified_time):
                print(f"Skipping {file_name}, already up to date.")
            else:
                download_file(service, file_id, file_name, mime_type, parent_path)

if __name__ == '__main__':
    service = authenticate_drive()

    # Root folder for downloads
    drive_id = '0ALOacF1v2nLbUk9PVA'  # Replace with your shared drive ID
    root_folder_id = drive_id
    download_folder = './KInIT_drive_sync'

    # Download files recursively from the shared drive
    download_files_recursively(service, drive_id, root_folder_id, download_folder)
