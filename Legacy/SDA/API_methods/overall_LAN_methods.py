from SDA.API_methods.url import DNA_CENTER_API_URL, DNA_CENTER_NETWORK_HEALTH, DNA_CENTER_CLIENT_HEALTH, \
    DNA_CENTER_ISSUES, DNA_CENTER_NODE_INFO
from Authentication.authentication import dnac_authenticate
from Legacy.Authentication.credentials import DNA_CENTER_BASE_URL
from pprint import pprint as pp


# TODO
# session = dnac_authenticate()
session = None


def get_dnac_network_health():
    """
    Gets LAN-wide aggregated network health in SD-Access fabric.

    :return: dict{} containing LAN-wide aggregated health metrics
    Fields:
    """
    # query parameters
    DNAC_NETWORK_HEALTH_URL = DNA_CENTER_BASE_URL + DNA_CENTER_API_URL + DNA_CENTER_NETWORK_HEALTH

    params = {}
    response = session.get(DNAC_NETWORK_HEALTH_URL, params=params, verify=False)
    response_dict = response.json()
    return response_dict


def get_dnac_client_health():
    """
    Gets LAN-wide aggregated client health in SD-Access fabric.

    :return: dict{} containing LAN-wide aggregated client health metrics
    Fields:
    """
    # query parameters
    DNAC_CLIENT_HEALTH_URL = DNA_CENTER_BASE_URL + DNA_CENTER_API_URL + DNA_CENTER_CLIENT_HEALTH

    params = {}
    response = session.get(DNAC_CLIENT_HEALTH_URL, params=params, verify=False)
    response_dict = response.json()
    return response_dict["response"][0]["scoreDetail"]


def get_dnac_issues():
    """
    Gets LAN-wide issues in SD-Access fabric.

    :return: dict{} containing LAN-wide aggregated client health metrics
    Fields:
    """
    # query parameters
    DNAC_ISSUES_URL = DNA_CENTER_BASE_URL + DNA_CENTER_API_URL + DNA_CENTER_ISSUES

    params = {}
    response = session.get(DNAC_ISSUES_URL, params=params, verify=False)
    response_dict = response.json()
    return response_dict


def get_dnac_node_info():
    """
    Gets SDA node(s) information in SD-Access fabric.

    :return: dict{} containing information about SDA Controller Node
    Fields:
    """
    # query parameters
    DNAC_NODE_INFO_URL = DNA_CENTER_BASE_URL + DNA_CENTER_API_URL + DNA_CENTER_NODE_INFO

    params = {}
    response = session.get(DNAC_NODE_INFO_URL, params=params, verify=False)
    response_dict = response.json()
    return response_dict["response"]


if __name__ == '__main__':
    network_health = get_dnac_network_health()
    client_health = get_dnac_client_health()
    issues = get_dnac_issues()
    dnac_nodes = get_dnac_node_info()
    pp(client_health)
