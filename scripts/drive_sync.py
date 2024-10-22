from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os.path

from googleapiclient.http import MediaIoBaseDownload

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


# Download a file from Google Drive
def download_file(service, file_id, file_name, local_folder):
    request = service.files().get_media(fileId=file_id)
    file_path = os.path.join(local_folder, file_name)

    with open(file_path, 'wb') as fh:
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            print(f"Downloading {file_name} {int(status.progress() * 100)}%.")
    return file_path


# List and download files from the shared folder
def list_and_download_files(service, folder_id, local_folder):
    if not os.path.exists(local_folder):
        os.makedirs(local_folder)

    results = service.files().list(
        q=f"'{folder_id}' in parents",
        fields="nextPageToken, files(id, name, mimeType)"
    ).execute()

    items = results.get('files', [])
    if not items:
        print('No files found in the shared folder.')
    else:
        for item in items:
            file_name = item['name']
            mime_type = item['mimeType']
            file_id = item['id']

            file_path = download_file(service, file_id, file_name, local_folder)
            print(f"File: {file_name}, Path: {file_path}, Type: {mime_type}")

    return {item['id']: item['name'] for item in items}


if __name__ == '__main__':
    service = authenticate_drive()

    # Set the shared folder ID and sync folder path
    folder_id = '0ALOacF1v2nLbUk9PVA'  # Replace with your shared folder ID
    local_sync_folder = './sync_folder'

    # Download all files from the shared folder
    list_and_download_files(service, folder_id, local_sync_folder)
