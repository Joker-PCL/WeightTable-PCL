from __future__ import print_function
import pickle
import os.path
from googleapiclient import errors
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

credentials_path = 'D:\\Project VS Code\\GitHub\\WeightTable-PCL\\poligram\\database\\client_secret.json'
script_id = 'AKfycby7SQq5nAAmokrkEuAjt8ewn0F6RGMhvtTSYPfp-bZFfy_uFmuiI2oIfiAAb6kfGO7C'


def main():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path, SCOPES)
            creds = flow.run_local_server()
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('script', 'v1', credentials=creds)

    try:
        request = {
            'function': "duplicate",
            'parameters': [],
            'devMode': True
        }
        response = service.scripts().run(body=request, scriptId=script_id).execute()
        print(response)
    except errors.HttpError as error:
        print(error.content)


if __name__ == '__main__':
    main()
