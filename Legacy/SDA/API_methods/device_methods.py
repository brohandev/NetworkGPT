from SDA.API_methods.url import DNA_CENTER_API_URL, DNA_CENTER_DEVICE_LIST_URI, \
    DNAC_INTERFACE_INFO_BY_DEVICEID_URI, DNAC_DEVICE_CONNECTED_DETAILS_URI, DNA_CENTER_DEVICE_HEALTH_URI, \
    DNAC_DEVICE_BY_ID_URI, DNAC_NODES_CONFIG_URI
from Authentication.authentication import dnac_authenticate
from Legacy.Authentication.credentials import DNA_CENTER_BASE_URL
from pprint import pprint as pp


# TODO
# session = dnac_authenticate()
session = None


def get_dnac_device_list(**device_fields):
    """
    Gets list of network devices based on filter criteria such as management IP address, mac address, hostname,
    etc. You can use the .* in any value to conduct a wildcard search. For example, to find all hostnames beginning
    with myhost in the IP address range 192.25.18.n, issue the following request: GET
    /dna/intent/api/v1/network-device?hostname=myhost.*&managementIpAddress=192.25.18..* If id parameter is provided
    with comma separated ids, it will return the list of network-devices for the given ids and ignores the other
    request parameters. You can also specify offset & limit to get the required list.

    :param: (dict{}) (case-insensitive) (optional)
    1. hostname (e.g.,C9300L-48P-2-Edge.cxsdasdwan.com)
    2. managementIpAddress (e.g., 10.80.1.11)
    3. macAddress (e.g., 80:2d:bf:e7:86:8b)
    4. locationName
    5. serialNumber (e.g., TTM24300A7J)
    6. location
    7. family (e.g., Switches and Hubs)
    8. type (e.g., Cisco Catalyst 9300L Switch Stack)
    9. series (e.g., Cisco Catalyst 9800 Series Wireless Controllers)
    10. collectionStatus (e.g., Managed)
    11. collectionInterval (e.g., Global Default)
    12. notSyncedForMinutes
    13. errorCode
    14. errorDescription
    15. softwareVersion (e.g., 17.3.4)
    16. softwareType (e.g., IOS-XE)
    17. platformId (e.g., C9800-40-K9)
    18. role (e.g., ACCESS)
    19. reachabilityStatus (e.g., Reachable)
    20. upTime (e.g., 8 days, 18:37:08.44)
    21. associatedWlcIp
    22. license.name
    23. license.type
    24. license.status
    25. module+name
    26. module+equpimenttype
    27. module+servicestate
    28. module+vendorequipmenttype
    29. module+partnumber
    30. module+operationstatecode
    31. id (e.g., 1f39066a-8ab2-41bf-894f-586521bb3a4f)
    32. deviceSupportLevel (e.g., Supported)
    33. offset
    34. limit
    :return: (list[]) list containing SDA devices represented as nested dict() objects
    """

    # query parameters
    DNAC_DEVICE_LIST_URL = DNA_CENTER_BASE_URL + DNA_CENTER_API_URL + DNA_CENTER_DEVICE_LIST_URI
    params = {}
    for field, value in device_fields.items():
        params[field] = value

    response = session.get(DNAC_DEVICE_LIST_URL, params=params, verify=False)
    response_dict = response.json()
    return response_dict["response"]


def get_dnac_nodes_config():
    """
    Gets config details of all DNAC nodes participating in SD-Access fabric.

    :param:
    1. None
    :return: (list[]) list containing device config represented as nested dict() objects
    Fields:
    """
    # query parameters
    DNAC_NODES_CONFIG_URL = DNA_CENTER_BASE_URL + DNA_CENTER_API_URL + DNAC_NODES_CONFIG_URI

    params = {}
    response = session.get(DNAC_NODES_CONFIG_URL, params=params, verify=False)
    response_dict = response.json()
    return response_dict['response']['nodes']


def get_dnac_device_health_list(**device_fields):
    """
    Gets list of network devices and their health statistics based on filter criteria such as management IP address,
    mac address, hostname, etc. You can use the .* in any value to conduct a wildcard search.

    :param: (dict{}) (case-insensitive) (optional)
    1. name (e.g.,C9300L-48P-2-Edge.cxsdasdwan.com)
    2. IpAddress (e.g., 10.80.1.11)
    3. macAddress (e.g., 80:2d:bf:e7:86:8b)
    4. osVersion (e.g., 17.3.4)
    5. overallHealth (e.g., 10)
    6. issueCount (e.g. 1)
    7. deviceFamily (e.g., Switches and Hubs)
    8. deviceType (e.g., Cisco Catalyst 9300L Switch Stack)
    9. interfaceLinkErrHealth (e.g., 10)
    10. cpuUlitilization (e.g., 10)
    11. cpuHealth (e.g., 10)
    12. memoryUtilizationHealth (e.g., 10)
    13. memoryUtilization (e.g., 66.36657928302309)
    14. interDeviceLinkAvailHealth (e.g., 100)
    15. interDeviceLinkAvailFabric (e.g., 10)
    16. reachabilityHealth (e.g. REACHABLE)

    :return: (list[]) list containing SDA devices' health statistics represented as nested dict() objects
    """

    # query parameters
    DNAC_DEVICE_HEALTH_LIST_URL = DNA_CENTER_BASE_URL + DNA_CENTER_API_URL + DNA_CENTER_DEVICE_HEALTH_URI
    params = {}
    for field, value in device_fields.items():
        params[field] = value

    response = session.get(DNAC_DEVICE_HEALTH_LIST_URL, params=params, verify=False)
    response_dict = response.json()
    return response_dict["response"]


def get_dnac_device_interface_info(device_id):
    """
    Gets interface details of specified network device participating in SD-Access fabric.

    :param:
    1. (string) (required) deviceUuid (e.g., 4f95a157-aea8-4529-bdac-ab6cda93c367)
    :return: (list[]) list containing device config represented as nested dict() objects
    Fields:
    """
    # query parameters
    DNAC_DEVICE_INTERFACE_INFO_URL = DNA_CENTER_BASE_URL + DNA_CENTER_API_URL + \
                            DNAC_INTERFACE_INFO_BY_DEVICEID_URI.format(deviceId=device_id)

    params = {}
    response = session.get(DNAC_DEVICE_INTERFACE_INFO_URL, params=params, verify=False)
    response_dict = response.json()
    return response_dict['response']


def get_dnac_connected_device_detail(device_id, interface_id):
    """
    Gets details of devices connected to specified device participating in SD-Access fabric.

    :param:
    1. (string) (required) deviceUuid (e.g., 4f95a157-aea8-4529-bdac-ab6cda93c367)
    2. (string) (required) interfaceUuid (e.g., )
    :return: (list[]) list containing details of devices connected to specified device represented as nested dict() objects

    Fields: capabilities:[], neighborDevice, neighborPort
    """
    # query parameters
    DNAC_DEVICE_CONNECTED_URL = DNA_CENTER_BASE_URL + DNA_CENTER_API_URL + \
                              DNAC_DEVICE_CONNECTED_DETAILS_URI.format(deviceUuid=device_id, interfaceUuid=interface_id)
    params = {}
    response = session.get(DNAC_DEVICE_CONNECTED_URL, params=params, verify=False)
    response_dict = response.json()
    return response_dict["response"]


def get_hostname_by_device_id(device_id):
    """
    Queries SDA with device UUID to retrieve hostname of the switch
    :return: (str) hostname of the device
    """
    # query parameters
    DNAC_DEVICE = DNA_CENTER_BASE_URL + DNA_CENTER_API_URL + \
                                DNAC_DEVICE_BY_ID_URI.format(id=device_id)
    params = {}
    response = session.get(DNAC_DEVICE, params=params, verify=False)
    response_dict = response.json()
    return response_dict["response"]["hostname"]


if __name__ == '__main__':
    # device_list = get_dnac_device_list(managementIpAddress=["10.8.1.5", "10.8.1.6"], family="Switches and Hubs")
    # device_list = get_dnac_device_list()
    # device_interface_info_SW = get_dnac_device_interface_info(
    #     device_id="826bc2f3-bf3f-465b-ad2e-e5701ff7a46c")  # SW4
    # device_interface_info_SW = get_dnac_device_interface_info(
    #     device_id="366692a9-a549-42ae-9033-15127d3729ab")  # Border Switch 10.8.1.2
    # device_interface_info_AP = get_dnac_device_interface_info(device_id="c7477498-fe69-4bba-a780-e56f72fc05c2")  # AP
    # device_interface_info_WLC = get_dnac_device_interface_info(device_id="030e672b-3b5c-44bf-a44a-7f7da09da9bb")  # WLC
    # hostname = get_hostname_by_device_id("826bc2f3-bf3f-465b-ad2e-e5701ff7a46c")
    pp(get_dnac_nodes_config())
