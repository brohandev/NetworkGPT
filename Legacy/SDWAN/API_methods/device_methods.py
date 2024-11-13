from Authentication.authentication import vmanage_authenticate
from Legacy.Authentication.credentials import VMANAGE_BASE_URL, VMANAGE_API_URL
from SDWAN.API_methods.url import VMANAGE_DEVICE_LIST_URI, VMANAGE_DEVICE_STATUS_URI, \
    VMANAGE_DEVICE_INTERFACE_INFO_URI
from pprint import pprint as pp

# TODO
# session = vmanage_authenticate()
session = None


def get_vmanage_device_list():
    """
    Retrieve and return network devices list. Returns information about each device that is part of the fabric.
    :param: None
    :return: (list[]) list containing SDWAN devices represented as dict() objects
    """
    url = VMANAGE_BASE_URL + VMANAGE_API_URL + VMANAGE_DEVICE_LIST_URI
    response = session.get(url=url, verify=False)
    sdwan_device_list = []

    if response.ok:
        sdwan_device_list = response.json()['data']
    else:
        print(response.status_code)
        print("Failed to get list of devices " + str(response.text))

    return sdwan_device_list


def get_vmanage_device_interface_info(system_ip):
    """
    Retrieve and return information about interface status of specified network device in SD-WAN fabric
    :param: (string) system_ip
    :return: (list[]) list containing interface information of each SDWAN device represented as a dict() object
    """
    device_status = None
    url = VMANAGE_BASE_URL + VMANAGE_API_URL + VMANAGE_DEVICE_INTERFACE_INFO_URI.format(system_ip=system_ip)

    response = session.get(url=url, verify=False)
    if response.ok:
        device_status = response.json()['data']
    else:
        print("Failed to get system status " + str(response.text))

    return device_status


def get_vmanage_device_status(system_ip):
    """
    Retrieve and return information about System status of specified network device in SD-WAN fabric
    :param: (string) system_ip
    :return: (list[]) list containing status information of each SDWAN device represented as a dict() object
    """
    device_status = None
    url = VMANAGE_BASE_URL + VMANAGE_API_URL + VMANAGE_DEVICE_STATUS_URI.format(system_ip=system_ip)

    response = session.get(url=url, verify=False)
    if response.ok:
        device_status = response.json()['data'][0]
    else:
        print("Failed to get system status " + str(response.text))

    return device_status
