import os
import pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from src.paths import TOKEN_PICKLE_PATH, CLIENT_SECRETS_PATH


if __name__ == "__main__":
# token.pickle stores the user's credentials from previously successful logins
    if os.path.exists(TOKEN_PICKLE_PATH):
        print('Loading Credentials From File...')
        with open(TOKEN_PICKLE_PATH, 'rb') as token:
            credentials = pickle.load(token)
    else:
        credentials = None
        print('No credentials found')

# If there are no valid credentials available, then either refresh the token or log in.
    if not credentials or not credentials.valid:
        try:
            if credentials.expired and credentials.refresh_token:
                print('Refreshing Access Token...')
                credentials.refresh(Request())
        except:
            print('Fetching New Tokens...')
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRETS_PATH,
                scopes=[
                    'https://www.googleapis.com/auth/youtube.upload'
                ]
            )
            flow.run_local_server(host="localhost", bind_addr="0.0.0.0", port=8080)
            credentials = flow.credentials

            # Save the credentials for the next run
            with open(TOKEN_PICKLE_PATH, 'wb') as f:
                print('Saving Credentials for Future Use...')
                pickle.dump(credentials, f)