from pytube import YouTube
import os
import certifi
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.urllib3 import AuthorizedHttp


SCOPES = ['https://www.googleapis.com/auth/youtube.readonly']

def get_authenticated_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secrets.json', SCOPES)
            creds = flow.run_local_server(port=8080)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

url_chapters = {}

url_chapters["pFssgtp1ckQ"] = "\n0:00 Why Use A Vest?\n2:18 Day 1: Finding Projects\n3:50 Day 2: Showing Crew & Projects\n10:40 Day 3: An Unexpected Turn Of Events\n13:13 Day 4: Volume Session\n13:52 Day 5: Getting Tired\n15:10 Day 6: Exhausted\n17:05 The Problems With Training Too Much\n18:06 Pros & Cons"
url_chapters["PvRbGuSeI3o"] = "\n00:00- intro \n00:20- turkey salad with poppyseed dressing\n04:08- beef meatloaf\n07:49- chicken and fried rice\n12:19- spaghetti squash (vegetarian option)\n17:23- taste testing\n20:34- let me know\n21:03- the end"

os.environ['SSL_CERT_FILE'] = certifi.where()

creds = get_authenticated_service()
authorized_http = AuthorizedHttp(creds)

#for i, (key, value) in enumerate(url_chapters.items()):
#    print(f"{key}:{key}")
keys_list = list(url_chapters.keys())
#print("http://youtube.com/watch?v="+keys_list[0])
url_first = "http://youtube.com/watch?v="
yt = YouTube(url=url_first+keys_list[0],
        proxies=None,
        use_oauth=True,
        allow_oauth_cache=True
    )

print(yt.title)

