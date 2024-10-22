from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os.path

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


# Function to list all shared drives
def list_shared_drives(service):
    try:
        response = service.drives().list().execute()
        drives = response.get('drives', [])

        if not drives:
            print('No shared drives found.')
        else:
            print('Shared drives:')
            for drive in drives:
                print(f"Name: {drive['name']}, ID: {drive['id']}")
    except Exception as e:
        print(f"An error occurred: {e}")


# Function to list all files in a specific shared drive
def list_files_in_shared_drive(service, drive_id):
    try:
        # List files in the given shared drive (KInIT)
        query = f"'{drive_id}' in parents"
        response = service.files().list(q=query, corpora='drive', driveId=drive_id, includeItemsFromAllDrives=True,
                                        supportsAllDrives=True,
                                        fields="nextPageToken, files(id, name, mimeType)").execute()

        files = response.get('files', [])

        if not files:
            print(f'No files found in the drive with ID: {drive_id}.')
        else:
            print(f'Files in drive ID {drive_id}:')
            for file in files:
                print(f"File Name: {file['name']}, File ID: {file['id']}, MIME Type: {file['mimeType']}")
    except Exception as e:
        print(f"An error occurred while listing files: {e}")


if __name__ == '__main__':
    service = authenticate_drive()

    # List shared drives first
    list_shared_drives(service)

    # List all files in the "KInIT" shared drive (ID: 0ALOacF1v2nLbUk9PVA)
    drive_id = '0ALOacF1v2nLbUk9PVA'  # Replace with the actual drive ID of "KInIT"
    list_files_in_shared_drive(service, drive_id)