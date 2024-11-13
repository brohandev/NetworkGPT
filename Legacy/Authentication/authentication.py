import json
import logging
import warnings

import requests
from pprint import pprint as pp
from requests.exceptions import HTTPError, ConnectionError, Timeout, RequestException
from urllib3.exceptions import InsecureRequestWarning

from Legacy.Authentication.credentials import DNA_CENTER_AUTH_URL, DNA_CENTER_ENCODED_AUTH, VMANAGE_AUTH_SESSION_URL, \
    VMANAGE_AUTH_TOKEN_URL, VMANAGE_USERNAME, VMANAGE_PASSWORD, ISE_BASE_URL, ISE_ENCODED_AUTH, \
    ISE_APISERVICE_METHOD, OPENAI_API_KEY, OPENAI_COMPLETION_URL, OPENAI_MODEL, OPENAI_TEMPERATURE, SNA_BASE_URL, \
    SNA_AUTH_TOKEN_URL, SNA_USERNAME, SNA_PASSWORD

log = logging.getLogger(__name__)
warnings.filterwarnings("ignore", category=InsecureRequestWarning)


def dnac_authenticate():
    """
        Creates a Session object and authenticates with the vManage node. A GET call is made to retrieve SDA X-Auth
        token. Upon successful retrieval, the Session object is updated with the X-Auth field in the header and returned
        to the caller. Upon failure during the previous step, the program stops and exits.
    """

    session = requests.Session()
    dnac_x_auth_token = None

    payload = {}
    headers = {
        "Content-Type": "application/json",
        # "Accept": "application/json"
    }

    try:
        response = requests.post(DNA_CENTER_AUTH_URL,
                                 auth=DNA_CENTER_ENCODED_AUTH,
                                 headers=headers,
                                 data=payload,
                                 verify=False)
        if response.ok:
            dnac_x_auth_token = response.json()["Token"]
        else:
            log.error("SDA Authentication: Failed to retrieve SDA X-Auth Token")
            exit()
    except:
        log.error("SDA Authentication: Failed to make a POST request to SDA API. Check URL and Credentials")
        exit()

    session.headers.update({"X-Auth-Token": dnac_x_auth_token})
    log.info("SDA Authentication: Authentication Successful")

    return session


def vmanage_authenticate():
    """
        Creates a Session object and authenticates with the vManage node. 2 separate GET requests are made to retrieve
        Session_ID and X-XRF Token. Upon successful retrieval, the Session object is updated with the 2 fields in the
        header and returned to the caller. Upon failure during any of the previous steps, the program stops and exits.
    """

    session = requests.Session()
    vmanage_session_id = None
    vmanage_x_xsrf_token = None

    payload = {
        "j_username": VMANAGE_USERNAME,
        "j_password": VMANAGE_PASSWORD
    }

    try:
        response = requests.post(url=VMANAGE_AUTH_SESSION_URL,
                                 data=payload,
                                 verify=False)
        if response.ok:
            cookies = response.headers["Set-Cookie"]
            vmanage_session_id = cookies.split(";")[0]
            # print("vManage Session ID: " + vmanage_session_id)
        else:
            log.error("vManage Authentication Failed: Retrieving Session ID")
            exit()

        response = requests.get(url=VMANAGE_AUTH_TOKEN_URL,
                                headers={"Cookie": vmanage_session_id},
                                verify=False)
        if response.ok:
            vmanage_x_xsrf_token = response.text
        else:
            log.error("vManage Authentication Failed: Retrieving Session Token")
            exit()
    except:
        log.error("vManage Authentication: Failed to make a POST request to vManage API. Check URL and Credentials")
        exit()

    if vmanage_x_xsrf_token is not None:
        # print("vManage XSRF Token: " + vmanage_x_xsrf_token)
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Cookie': vmanage_session_id,
            'X-XSRF-TOKEN': vmanage_x_xsrf_token
        }
    else:
        headers = {
            'Content-Type': "application/json",
            'Cookie': vmanage_session_id
        }

    session.headers.update(headers)
    log.info("vManage Authentication: Authentication Successful")
    return session


def ise_authenticate():
    """
        Creates a Session object and authenticates with the primary ISE PAN node. Upon successful HTTP Status Code,
        updates Session object with the credentials and returns object to caller. Upon failure, attempts to enable API
        Gateway Service on all ISE nodes and re-attempts authentication. Upon failure during any of the previous steps,
        the program stops and exits.
    """
    response = None
    update_response = None
    session = requests.Session()

    try:
        response = requests.get(url=ISE_BASE_URL + ISE_APISERVICE_METHOD + "/get",
                                auth=ISE_ENCODED_AUTH,
                                headers={
                                    'Content-Type': 'application/json',
                                    'Accept': 'application/json'
                                },
                                verify=False)
        if response.ok:
            session.auth = ISE_ENCODED_AUTH
            session.verify = False
            headers = {
                'Content-Type': "application/json",
                'Accept': 'application/json'
            }
            session.headers.update(headers)

            disabled_ise_nodes = []
            for response_dict in response.json():
                if not response_dict["isEnabled"]:
                    disabled_ise_nodes.append(response_dict["hostname"])
                    log.debug(f'ISE Node {response_dict["hostname"]} has disabled API Gateway Service...')

            log.info(f'Enabling API Gateway Service for all ISE Nodes...')
            update_response = requests.post(url=ISE_BASE_URL + ISE_APISERVICE_METHOD + "/update",
                                            auth=ISE_ENCODED_AUTH,
                                            headers={
                                                "Accept": "application/json",
                                            },
                                            json=[
                                                {
                                                    "hostname": f"{hostname}",
                                                    "isEnabled": True
                                                } for hostname in disabled_ise_nodes
                                            ],
                                            verify=False)
            if not update_response.ok:
                update_response.raise_for_status()
            else:
                log.info('All ISE Nodes are Enabled for API Gateway Service...')
        else:
            response.raise_for_status()

    except HTTPError:
        if response.status_code == 403 or update_response.status_code == 403:
            log.error('\nYou do not have the required access to ISE data'
                          'Please turn on your AnyConnect VPN. \n\n')
        exit()
    except ConnectionError as errc:
        log.error('\nError: ' + str(errc))
        exit()

    except Timeout as errt:
        log.error('\nError: ' + str(errt))
        exit()

    except RequestException as err:
        log.error('\nError: ' + str(err))
        exit()

    return session


def openAI_authenticate():
    """
        Creates a Session object and authenticates with the OpenAI servers. A POST call is made to test if the request
        complies with OpenAI's accepted API syntax. Upon successful status code, the Session object is updated with the
        Bearer Token in the header and returned to the caller. Upon failure during the previous step, the program stops
        and exits.
    """
    response = None
    session = requests.Session()

    try:
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        response = requests.post(url=OPENAI_COMPLETION_URL,
                                 headers=headers,
                                 data=json.dumps({
                                     "model": OPENAI_MODEL,
                                     "messages": [
                                         {
                                             "role": "user",
                                             "content": "Say this is a test!"
                                         }
                                     ],
                                     "temperature": OPENAI_TEMPERATURE
                                 }),
                                 verify=False)

        if response.ok and response:
            session.headers.update(headers)
            log.info("ChatGPT Authentication: Authentication Successful")
        else:
            response.raise_for_status()

    except HTTPError:
        if response.status_code == 403:
            log.error('\nYou do not have the required access to OpenAI servers'
                          'Please check/refresh your API key. \n\n')
            exit()
    except ConnectionError as errc:
        log.error('\nError: ' + str(errc))
        exit()

    except Timeout as errt:
        log.error('\nError: ' + str(errt))
        exit()

    except RequestException as err:
        log.error('\nError: ' + str(err))
        exit()

    return session


def authenticate_stealthwatch():
    session = requests.Session()

    url = SNA_BASE_URL + SNA_AUTH_TOKEN_URL
    login_request_data = {
        "username": SNA_USERNAME,
        "password": SNA_PASSWORD
    }

    response = session.post(url=url, verify=False, data=login_request_data)

    try:
        if response.ok:
            # Set XSRF token for future requests
            for cookie in response.cookies:
                if cookie.name == 'XSRF-TOKEN':
                    XSRF_TOKEN = cookie.value
                    session.headers.update({'X-XSRF-TOKEN': XSRF_TOKEN})
                    break
        else:
            response.raise_for_status()

    except HTTPError:
        if response.status_code == 400:
            log.error('\nEither missing authentication token and the client should retry authentication, or request '
                      'parameters are invalid')
            exit()
        if response.status_code == 401:
            log.error('\nExpired or invalid authentication token; client should re-authenticate')
            exit()
        if response.status_code == 403:
            log.error('\nYou do not have the required access to Stealthwatch data. Please enable your appropriate '
                      'AnyConnect VPN or adjust admin permissions.')
            exit()
        if response.status_code == 404:
            log.error('\nResource not found, invalid or inaccessible path parameters.')
            exit()
    except ConnectionError:
        log.error("SNAM Authentication: Connection: Check network connectivity to SNAM node or check URL validity.")
        exit()
    except Timeout:
        log.error("SNAM Authentication: Timeout: Re-attempt authentication method.")
        exit()
    except Exception as e:
        log.error(f"SNAM Authentication: Unknown exception: Deeper troubleshooting required to fix {e}")
        exit()

    return session


def authenticate_controller():
    dnac_session = dnac_authenticate()
    vmanage_session = vmanage_authenticate()
    ise_session = ise_authenticate()
    sw_session = authenticate_stealthwatch()

    return dnac_session, vmanage_session, ise_session, sw_session


if __name__ == '__main__':
    # authenticate()
    # dnac_session = dnac_authenticate()
    vmanage_session = vmanage_authenticate()
    # sw_session = authenticate_stealthwatch()

