from Authentication.authentication import authenticate_stealthwatch
from Legacy.Authentication.credentials import SNA_BASE_URL
from Auxiliary.shared_functions import python_datetime_converter
from Stealthwatch.API_methods.url import SNA_TENANTS_URI, SNA_INTERNAL_HOSTS_ALARMS_URI, SNA_EXTERNAL_HOSTS_ALARMS_URI, \
    SNA_INTERNAL_HOSTS_TAGS_URI, SNA_EXTERNAL_HOSTS_TAGS_URI, SNA_CUSTOM_HOSTS_TAGS_URI, SNA_SECURITY_EVENTS_URI
from pprint import pprint as pp

# TODO
# session = authenticate_stealthwatch()
session = None


def get_sna_tenant():
    """
        Retrieves and return list of tenant IDs in SNA.
        :param: None
        :return: (int) SNA tenant ID represented as integer
    """
    url = SNA_BASE_URL + SNA_TENANTS_URI
    response = session.get(url=url, verify=False)
    tenant_id = None
    try:
        if response.ok:
            tenant_id = sorted(response.json()['data'], key=lambda d: d['id'])
        else:
            response.raise_for_status()
    except:
        print(response.status_code)
        print("Failed to retrieve SNA tenant ID " + str(response.text))

    return tenant_id[0]['id']


def get_sna_host_tag_mapping():
    # tenant_id = get_sna_tenant()
    tenant_id = 301
    mapping = []

    # Retrieve Internal Host Tags
    url = SNA_BASE_URL + SNA_INTERNAL_HOSTS_TAGS_URI.format(tenantId=tenant_id)
    response = session.get(url=url, verify=False)
    try:
        if response.ok:
            mapping.extend(response.json()['data'])
        else:
            response.raise_for_status()
    except:
        print(response.status_code)
        print("Failed to retrieve SNA Internal Host Tag Mappings " + str(response.text))

    # Retrieve External Host Tags
    url = SNA_BASE_URL + SNA_EXTERNAL_HOSTS_TAGS_URI.format(tenantId=tenant_id)
    response = session.get(url=url, verify=False)
    try:
        if response.ok:
            mapping.extend(response.json()['data'])
        else:
            response.raise_for_status()
    except:
        print(response.status_code)
        print("Failed to retrieve SNA External Host Tag Mappings " + str(response.text))

    # Retrieve Custom Host Tags
    url = SNA_BASE_URL + SNA_CUSTOM_HOSTS_TAGS_URI.format(tenantId=tenant_id)
    response = session.get(url=url, verify=False)
    try:
        if response.ok:
            mapping.extend(response.json()['data'])
        else:
            response.raise_for_status()
    except:
        print(response.status_code)
        print("Failed to retrieve SNA Custom Host Tag Mappings " + str(response.text))

    return dict([(item["id"], item["displayName"]) for item in mapping])


def get_sna_host_tagname_from_id_list(id_list):
    host_tagname_list = []
    id_tag_mapping = get_sna_host_tag_mapping()

    for id in id_list:
        host_tagname_list.append(id_tag_mapping[id])

    return host_tagname_list


def get_sna_events():
    # tenant_id = get_sna_tenant()
    tenant_id = 301
    security_events = None

    # Retrieve Security Events
    url = SNA_BASE_URL + SNA_SECURITY_EVENTS_URI.format(tenantId=tenant_id)
    response = session.get(url=url, verify=False)
    try:
        if response.ok:
            security_events = dict([(item["id"], {"name": item["name"], "description": item["description"]}) for item in response.json()['data']])
        else:
            response.raise_for_status()
    except:
        print(response.status_code)
        print("Failed to retrieve SNA Security Events " + str(response.text))

    return security_events


def get_sna_event_name_from_id(id):
    id_event_mapping = get_sna_events()
    return id_event_mapping[id]


def get_sna_internal_hosts():
    """
        Retrieve and return top breaching internal hosts list. Returns information about each host
        breaching threshold values.
        :param: None
        :return: (list[]) list containing SNA hosts represented as dict() objects
    """
    # tenant_id = get_sna_tenant()
    tenant_id = 301

    url_internal_hosts = SNA_BASE_URL + SNA_INTERNAL_HOSTS_ALARMS_URI.format(tenantId=tenant_id)
    internal_hosts_response = session.get(url=url_internal_hosts, verify=False)
    try:
        if not internal_hosts_response.ok:
            internal_hosts_response.raise_for_status()
    except:
        print(internal_hosts_response.status_code)
        print("Failed to retrieve internal SNA hosts " + str(internal_hosts_response.text))

    return internal_hosts_response


def get_sna_external_hosts():
    """
        Retrieve and return top breaching external hosts list. Returns information about each host
        breaching threshold values.
        :param: None
        :return: (list[]) list containing SNA hosts represented as dict() objects
    """
    # tenant_id = get_sna_tenant()
    tenant_id = 301

    url_external_hosts = SNA_BASE_URL + SNA_EXTERNAL_HOSTS_ALARMS_URI.format(tenantId=tenant_id)
    external_hosts_response = session.get(url=url_external_hosts, verify=False)
    try:
        if not external_hosts_response.ok:
            external_hosts_response.raise_for_status()
    except:
        print(external_hosts_response.status_code)
        print("Failed to retrieve internal SNA hosts " + str(external_hosts_response.text))

    return external_hosts_response


if __name__ == '__main__':
    pp(get_sna_tenant())
    # pp(get_sna_host_tag_mapping())
    # pp(get_sna_host_tagname_from_id_list([50082,1,3,5,23,50083,43,50036]))
