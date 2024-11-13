import json
import requests
from Legacy.Authentication.credentials import DNA_CENTER_BASE_URL
from pprint import pprint as pp

# TODO
# session = dnac_authenticate()
session = None


def get_dnac_client_list():
    """
    Gets details of all connected clients participating in SD-Access fabric.

    :param:
    1. None
    :return: (list[]) list containing client details represented as nested dict() objects
    Fields:
    """
    url = f"{DNA_CENTER_BASE_URL}/api/assurance/v1/host"
    payload = json.dumps({})
    session.headers.update({'Content-Type': 'application/json'})
    response = session.post(url, data=payload, verify=False)

    # TODO
    if 'response' in response.json().keys():
        return response.json()['response']
    else:
        return []


if __name__ == '__main__':
    pp(get_dnac_client_list())
