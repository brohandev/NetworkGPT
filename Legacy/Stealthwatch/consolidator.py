import logging
from pprint import pprint as pp

from Auxiliary.shared_functions import deduplicate_list, write_to_json, python_datetime_converter
from Excel.excel_controller import STEALTHWATCH_KB_PATH
from Stealthwatch.API_methods.alarm_methods import get_sna_events, get_sna_host_tag_mapping, \
    get_sna_internal_hosts, get_sna_external_hosts


log = logging.getLogger(__name__)


def get_sna_host_tagname_from_id_list(id_list):
    host_tagname_list = []
    id_tag_mapping = get_sna_host_tag_mapping()

    for id in id_list:
        if id in id_tag_mapping.keys():
            host_tagname_list.append(id_tag_mapping[id])
        else:
            host_tagname_list.append('Catch All')

    return host_tagname_list


def get_sna_event_name_from_id(id):
    id_event_mapping = get_sna_events()
    return id_event_mapping[id]


def consolidate_sw_top_hosts():
    """
        Retrieve and return top breaching internal and external hosts list. Returns information about each host
        breaching threshold values.
        :param: None
        :return: (list[]) list containing SNA hosts represented as dict() objects
    """
    internal_hosts_response = get_sna_internal_hosts()
    internal_hosts = []
    try:
        if internal_hosts_response is not None:
            json_response = internal_hosts_response.json()['data']
            for host_index in range(len(json_response['data'])):
                if not json_response['data'][host_index]['sourceSecurityEvents'] and \
                        not json_response['data'][host_index]['targetSecurityEvents']:
                    continue
                internal_hosts.append(
                    {
                        "host_ip_address": json_response['data'][host_index]['ipAddress'],
                        "host_type": "internal",
                        "host_security_tags": deduplicate_list(get_sna_host_tagname_from_id_list(json_response['data'][host_index]['hostGroupIds'])),
                        "source_security_events": [{
                            "name": get_sna_event_name_from_id(item['typeId'])['name'],
                            "description": get_sna_event_name_from_id(item['typeId'])['description'],
                            "severity": item['severity']
                        } for item in json_response['data'][host_index]['sourceSecurityEvents']],
                        "target_security_events": [{
                            "name": get_sna_event_name_from_id(item['typeId'])['name'],
                            "description": get_sna_event_name_from_id(item['typeId'])['description'],
                            "severity": item['severity']
                        } for item in json_response['data'][host_index]['targetSecurityEvents']],
                        "time_start": python_datetime_converter(json_response['header']['startTime']),
                        "time_end": python_datetime_converter(json_response['header']['endTime'])
                    }
                )
        else:
            internal_hosts = []
    except:
        print(internal_hosts_response.status_code)
        print("Failed to retrieve internal SNA hosts " + str(internal_hosts_response.text))

    external_hosts_response = get_sna_external_hosts()
    external_hosts = []
    try:
        if external_hosts_response is not None:
            json_response = external_hosts_response.json()['data']
            for host_index in range(len(json_response['data'])):
                if not json_response['data'][host_index]['sourceSecurityEvents'] and \
                        not json_response['data'][host_index]['targetSecurityEvents']:
                    continue
                external_hosts.append(
                    {
                        "host_ip_address": json_response['data'][host_index]['ipAddress'],
                        "host_type": "external",
                        "host_security_tags": deduplicate_list(get_sna_host_tagname_from_id_list(json_response['data'][host_index]['hostGroupIds'])),
                        "source_security_events": [{
                            "name": get_sna_event_name_from_id(item['typeId'])['name'],
                            "description": get_sna_event_name_from_id(item['typeId'])['description'],
                            "severity": item['severity']
                        } for item in json_response['data'][host_index]['sourceSecurityEvents']],
                        "target_security_events": [{
                            "name": get_sna_event_name_from_id(item['typeId'])['name'],
                            "description": get_sna_event_name_from_id(item['typeId'])['description'],
                            "severity": item['severity']
                        } for item in json_response['data'][host_index]['targetSecurityEvents']],
                        "time_start": python_datetime_converter(json_response['header']['startTime']),
                        "time_end": python_datetime_converter(json_response['header']['endTime'])
                    }
                )

        else:
            external_hosts = []
    except:
        print(external_hosts_response.status_code)
        print("Failed to retrieve external SNA hosts " + str(external_hosts_response.text))

    return internal_hosts + external_hosts


def consolidate_sw_information():
    """
        Generate a single json object containing all information about top hosts breaching alarms from Stealthwatch
        :return:
    """
    sw_information = {
        "STEALTHWATCH_ALARMS": consolidate_sw_top_hosts()
    }

    return sw_information


def generate_SW_KB():
    # try:
    sw_information = consolidate_sw_information()
    write_to_json(document=STEALTHWATCH_KB_PATH, content=sw_information)
        # log.info("Stealthwatch KB Update: Update Successful")
    # except:
    #     log.info("Stealthwatch KB Update: Update Unsuccessful")


if __name__ == '__main__':
    generate_SW_KB()
    # pp(consolidate_sw_top_hosts())
