from google_auth_oauthlib.flow import InstalledAppFlow
import os

def generate_gmail_token(
    credentials_path: str = "credentials.json",
    token_path:       str = "token.json"
):
    # 1) Define the Gmail scope you need
    SCOPES = ["https://www.googleapis.com/auth/gmail.compose"]

    # 2) Create the flow using your downloaded credentials.json
    flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)

    # 3) Launch a local server to complete the OAuth login in your browser
    creds = flow.run_local_server(port=0)

    # 4) Save the resulting token.json for your app to use
    # os.makedirs(os.path.dirname(token_path), exist_ok=True)
    with open(token_path, "w") as token_file:
        token_file.write(creds.to_json())
    print(f"✅ token.json created at {token_path}")

if __name__ == "__main__":
    generate_gmail_token()
