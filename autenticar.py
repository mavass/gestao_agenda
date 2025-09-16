from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import streamlit as st
import os

SCOPES = ['https://www.googleapis.com/auth/calendar']


def autenticar_gmail():
    return _autenticar_google('gmail')


def autenticar_laudite():
    return _autenticar_google('laudite')


def _autenticar_google(servico):
    creds = Credentials(
    None,
    refresh_token=st.secrets[servico]["refresh_token"],
    token_uri="https://oauth2.googleapis.com/token",
    client_id=st.secrets[servico]["client_id"],
    client_secret=st.secrets[servico]["client_secret"]
    )
    return build('calendar', 'v3', credentials=creds)

# def autenticar_laudite():
#     creds = None
#     if os.path.exists('token_laudite.json'):
#         creds = Credentials.from_authorized_user_file('token_laudite.json', SCOPES)
#     if not creds or not creds.valid:
#         if creds and creds.expired and creds.refresh_token:
#             creds.refresh(Request())
#         else:
#             flow = InstalledAppFlow.from_client_secrets_file('credentials_laudite.json', SCOPES)
#             creds = flow.run_local_server(port=0)
#         with open('token_laudite.json', 'w') as token:
#             token.write(creds.to_json())
#     return build('calendar', 'v3', credentials=creds)


# def autenticar_gmail():
#     creds = None
#     if os.path.exists('token_gmail.json'):
#         creds = Credentials.from_authorized_user_file('token_gmail.json', SCOPES)
#     if not creds or not creds.valid:
#         if creds and creds.expired and creds.refresh_token:
#             creds.refresh(Request())
#         else:
#             flow = InstalledAppFlow.from_client_secrets_file('credentials_gmail.json', SCOPES)
#             creds = flow.run_local_server(port=0)
#         with open('token_gmail.json', 'w') as token:
#             token.write(creds.to_json())
#     return build('calendar', 'v3', credentials=creds)
