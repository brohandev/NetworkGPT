from dotenv import dotenv_values
import os
from requests.auth import HTTPBasicAuth

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
ENV_DIR = BASE_DIR + "/.env"
credentials = dotenv_values(ENV_DIR)

# [SD-Access] DNA Center Credentials
DNA_CENTER_BASE_URL = credentials['DNA_CENTER_BASE_URL']
DNA_CENTER_USERNAME = credentials['DNA_CENTER_USERNAME']
DNA_CENTER_PASSWORD = credentials['DNA_CENTER_PASSWORD']
DNA_CENTER_ENCODED_AUTH = HTTPBasicAuth(
    username=DNA_CENTER_USERNAME,
    password=DNA_CENTER_PASSWORD
)

# [SD-WAN] vManage Credentials
VMANAGE_BASE_URL = credentials['VMANAGE_BASE_URL']
VMANAGE_USERNAME = credentials['VMANAGE_USERNAME']
VMANAGE_PASSWORD = credentials['VMANAGE_PASSWORD']

# [AAA Server] ISE Credentials
ISE_BASE_URL = credentials['ISE_BASE_URL']
ISE_APISERVICE_METHOD = "/admin/API/apiGateway"
ISE_USERNAME = credentials['ISE_USERNAME']
ISE_PASSWORD = credentials['ISE_PASSWORD']
ISE_ENCODED_AUTH = HTTPBasicAuth(
    username=ISE_USERNAME,
    password=ISE_PASSWORD
)

# [Threat Hunting Server] SNAM Credentials
SNA_BASE_URL = credentials['SNA_BASE_URL']
SNA_USERNAME = credentials['SNA_USERNAME']
SNA_PASSWORD = credentials['SNA_PASSWORD']

# [Knox Server] Samsung Phone Credentials
KNOX_BASE_URL = "https://ap01.manage.samsungknox.com/emm/oapi"
KNOX_AUTH_URL = "https://ap01.manage.samsungknox.com/emm/oauth/token?"
KNOX_CLIENT_ID = credentials['KNOX_CLIENT_ID']
KNOX_CLIENT_SECRET = credentials['KNOX_CLIENT_SECRET']

# [OpenAI Server] ChatGPT Credentials
OPENAI_API_KEY = credentials['OPENAI_API_KEY']
OPENAI_COMPLETION_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_MODEL = "gpt-4o"
OPENAI_TEMPERATURE = 0.7

# [Webex Server] Webex Bot Credentials
WEBEX_BOT_ACCESS_TOKEN = credentials['WEBEX_BOT_ACCESS_TOKEN']
WEBEX_BOT_NAME = "NetworkGPT"
WEBEX_RODEV_ROOM = credentials['WEBEX_RODEV_ROOM']
