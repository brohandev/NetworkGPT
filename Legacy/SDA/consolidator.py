import logging
from pprint import pprint as pp

from Auxiliary.shared_functions import generate_id_list, clean_json, epoch_datetime_converter, write_to_json
from SDA.API_methods.device_methods import get_dnac_device_list, get_dnac_device_interface_info, \
    get_dnac_connected_device_detail, get_dnac_device_health_list, get_hostname_by_device_id, get_dnac_nodes_config
from SDA.API_methods.client_methods import get_dnac_client_list
from SDA.API_methods.overall_LAN_methods import get_dnac_issues
from Excel.excel_controller import DNAC_KB_PATH

log = logging.getLogger(__name__)


def consolidate_lan_device_information():
    """
    1. Retrieve LAN device list and device-associated fields
    2. Generate list of device IDs
    3. Use device hostname to retrieve list of heatlh statistics per device
    4. Use device ID to retrieve list of interfaces per device
    5. Use interface ID to retrieve connected interface info and append to interface list info
    6. Append interface info list to corresponding device list info
    :return: (list[]) list containing device and interface information represented as nested dict() objects
    """
    device_list = []

    # Retrieve chassis details of each fabric device in SDA
    initial_device_list = get_dnac_device_list()
    for device in initial_device_list:
        stripped_device_dict = {k: device[k] for k in device.keys() & {
            'family',
            'type',
            'softwareType',
            'softwareVersion',
            'serialNumber',
            'upTime',
            'hostname',
            'managementIpAddress',
            'reachabilityStatus',
            'role',
            'id'
        }
                                }
        device_list.append(stripped_device_dict)

    # Retrieve health statistics of each device by hostname
    device_health_list = get_dnac_device_health_list()
    for device_detail_index in range(len(device_list)):
        for device_health_index in range(len(device_health_list)):
            if device_list[device_detail_index]["hostname"] == device_health_list[device_health_index]["name"]:
                stripped_dict_obj = {k: device_health_list[device_health_index][k]
                                     for k in device_health_list[device_health_index].keys() & {
                                         'overallHealth',
                                         'issueCount',
                                         'interfaceLinkErrHealth',
                                         'cpuUlitilization',
                                         'cpuHealth',
                                         'memoryUtilization',
                                         'memoryUtilizationHealth',
                                         'interDeviceLinkAvailHealth'
                                     }
                                     }
                device_list[device_detail_index].update(stripped_dict_obj)

    # Retrieve interface details of each device by device ID
    device_id_list = generate_id_list(obj_dict_list=device_list)
    clean_device_list = None
    for device_id in device_id_list:
        stripped_device_interfaces_list = []
        device_interfaces_list = get_dnac_device_interface_info(device_id=device_id)
        for dict_obj in device_interfaces_list:
            stripped_dict_obj = {k: dict_obj[k] for k in dict_obj.keys() & {
                'portName',
                'status',
                'mtu',
                'speed',
                'macAddress',
                'ipv4Address',
                'ipv4Mask',
                'id'
            }
                                 }
            stripped_device_interfaces_list.append(stripped_dict_obj)

        # Retrieve neighbour details connected to each interface of each device
        interface_id_list = generate_id_list(obj_dict_list=stripped_device_interfaces_list)
        for interface_id in interface_id_list:
            neighbour_dict = get_dnac_connected_device_detail(device_id=device_id, interface_id=interface_id)
            interface_index = next(
                i for i, item in enumerate(stripped_device_interfaces_list) if item["id"] == interface_id)
            if neighbour_dict is not None:
                stripped_device_interfaces_list[interface_index]["neighbour"] = \
                    {k: neighbour_dict[k] for k in neighbour_dict.keys() & {
                        'neighborDevice',
                        'neighborPort'
                    }
                     }
            else:
                stripped_device_interfaces_list[interface_index]["neighbour"] = {}

        device_index = next(i for i, item in enumerate(device_list) if item["id"] == device_id)
        device_list[device_index]["interfaces"] = stripped_device_interfaces_list

        clean_device_list = [clean_json(dict_obj) for dict_obj in device_list]

    # Retrieve chassis details of each DNAC node in SDA
    dnac_node_list = get_dnac_nodes_config()
    for dnac in dnac_node_list:
        clean_device_list.append(
            {
                'hostname': dnac['platform']['product'],
                'family': "DNA Center (DNAC)",
                'ipv4Addresses': [ip_dict_obj['inet']['host_ip'] for ip_dict_obj in dnac['network']
                                  if ip_dict_obj['inet']['host_ip']],
                'vendor': dnac['platform']['vendor'],
                'platform': dnac['platform']['provider'],
                'interfaces': []
            }
        )

    return clean_device_list


def consolidate_lan_issues():
    """
    1. Retrieve LAN-wide network health dict
    2. Retrieve LAN-wide client health dict
    3. Retrieve LAN-wide issues dict
    4. Retrieve SDA nodes information dict
    5. Consolidate abovementioned dicts into 1 overall health dict
    :return: dict{} containing LAN-wide health metrics
    """
    initial_network_issues = get_dnac_issues()
    network_issues_dict = {k: initial_network_issues[k] for k in initial_network_issues.keys() & {
        'totalCount',
        'response'
    }}
    issues = []
    for issue in network_issues_dict["response"]:
        stripped_issue_dict = {k: issue[k] for k in issue.keys() & {
            'name',
            'issueId',
            'deviceId',
            'status',
            'last_occurence_time'
        }}
        if stripped_issue_dict['deviceId'] == "":
            continue

        stripped_issue_dict['last_occurence_time'] = epoch_datetime_converter(
            stripped_issue_dict['last_occurence_time'] / 1000)

        stripped_issue_dict['deviceName'] = get_hostname_by_device_id(stripped_issue_dict['deviceId'])
        del stripped_issue_dict['deviceId']

        issues.append(stripped_issue_dict)

    return issues if issues else ["No Issues/Events/Problems in the LAN"]


def consolidate_client_information():
    initial_client_info = get_dnac_client_list()

    clients = []
    for initial_client_info_dict in initial_client_info:
        client_info_dict = {k: initial_client_info_dict[k] for k in initial_client_info_dict.keys() & {
            "connectionStatus",
            "hostType",
            "identifier",
            "healthScore",
            "hostIpV4",
            "hostMac",
            "vlanId",
            "l3VirtualNetwork",
            "location",
            "clientConnection",
            "port",
            "usage",
            "remoteEndDuplexMode",
        }}

        hostname = ""
        if client_info_dict["hostIpV4"] == "192.168.1.101":
            hostname = "CAM1"
        elif client_info_dict["hostIpV4"] == "192.168.1.102":
            hostname = "CAM2"
        elif client_info_dict["hostIpV4"] == "192.168.1.103":
            hostname = "CAM3"
        elif client_info_dict["hostIpV4"] == "192.168.1.100":
            hostname = "Network Video Recorder (NVR)"
        elif client_info_dict["hostIpV4"] == "192.168.1.106":
            hostname = "Laptop"

        clients.append({
            "hostname": hostname,
            "connection_status": client_info_dict["connectionStatus"],
            "connection_type": client_info_dict["hostType"],
            "host_id": client_info_dict["identifier"],
            "health_score": client_info_dict["healthScore"][0]["score"],
            "ip_address": client_info_dict["hostIpV4"],
            "mac_address": client_info_dict["hostMac"],
            "vlan": client_info_dict["vlanId"],
            "L3_virtual_network": client_info_dict["l3VirtualNetwork"],
            "location": client_info_dict["location"],
            "connected_device": client_info_dict["clientConnection"],
            "interface/port": client_info_dict["port"],
            "usage": str(client_info_dict["usage"] / 1048576) + "MB",
            "mode": client_info_dict["remoteEndDuplexMode"]
        })

    return clients


def consolidate_lan_information():
    """
    Generate a single json object containing all information about the LAN from SDA
    :return:
    """

    lan_information = {
        "LAN_DEVICES": consolidate_lan_device_information(),
        "CLIENTS": consolidate_client_information(),
        "LAN_ISSUES": consolidate_lan_issues()
    }

    cleaned_lan_information = clean_json(lan_information)
    return cleaned_lan_information


def generate_DNAC_KB():
    try:
        lan_information = consolidate_lan_information()
        write_to_json(document=DNAC_KB_PATH, content=lan_information)
        log.info("DNAC KB Update: Update Successful")
    except:
        log.info("DNAC KB Update: Update Unsuccessful")


if __name__ == '__main__':
    # pp(consolidate_lan_information())
    generate_DNAC_KB()
    # pp(consolidate_client_information())
