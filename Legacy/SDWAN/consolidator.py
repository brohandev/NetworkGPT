import logging
from pprint import pprint as pp

from Auxiliary.shared_functions import generate_id_list, clean_json, epoch_datetime_converter, write_to_json

from SDWAN.API_methods.device_methods import get_vmanage_device_list, get_vmanage_device_interface_info, \
    get_vmanage_device_status
from SDWAN.API_methods.issues_methods import get_vmanage_alarms
from Excel.excel_controller import VMANAGE_KB_PATH


log = logging.getLogger(__name__)


def consolidate_wan_device_information():
    """
    1. Retrieve WAN device list and device-associated fields
    2. Retrieve interface information per WAN device by system IP, append inerface information as a list of dict objects
    3.
    :return: (list[]) list containing device and interface information represented as nested dict() objects
    """
    # Retrieve device details of each device
    initial_device_list = get_vmanage_device_list()
    device_list = []
    for device in initial_device_list:

        stripped_device_dict = {k: device[k] for k in device.keys() & {
            'system-ip',
            'host-name',
            'reachability',
            'status',
            'device-type',
            'certificate-validity',
            'version',
            'site-id',
        }
                                }

        # Retrieve health statistics of each device by system IP
        device_status = get_vmanage_device_status(system_ip=stripped_device_dict['system-ip'])
        device_status = {k: device_status[k] for k in device_status.keys() & {
            'mem_total',
            'mem_free',
            'disk_size',
            'disk_avail',
            'reboot_reason',
            'uptime',
            'lastupdated'
        }
                         }
        device_status['lastupdated'] = epoch_datetime_converter(device_status['lastupdated'] / 1000)
        stripped_device_dict.update(device_status)

        # Retrieve details of each interface of each device by system IP
        device_interfaces_list = get_vmanage_device_interface_info(system_ip=stripped_device_dict['system-ip'])
        device_interfaces_list = [{k: interface[k] for k in interface.keys() & {
            'if-admin-status',
            'vpn-id',
            'mtu',
            'ip-address',
            'ipv4-subnet-mask',
            'speed-mbps'
        }
                                   } for interface in device_interfaces_list]
        stripped_device_dict["interfaces"] = device_interfaces_list

        device_list.append(stripped_device_dict)

    return device_list


def consolidate_wan_issues():
    # Retrieve issue details of each issue
    issues_list = get_vmanage_alarms()
    issues_list = [{k: issue[k] for k in issue.keys() & {
        'active',
        'system_ip',
        'id',
        'eventname',
        'message',
        'severity',
        'severity_number',
        'entry_time'
    }
                    } for issue in issues_list]

    issues_list = [issue for issue in issues_list if issue['active'] is True]

    return issues_list if issues_list else ["No Issues/Events/Problems in the WAN"]


def consolidate_wan_information():
    """
    Generate a single json object containing all information about the WAN from vManage
    :return:
    """

    wan_information = {
        "WAN_DEVICES": consolidate_wan_device_information(),
        "WAN_ISSUES": consolidate_wan_issues()
    }

    cleaned_wan_information = clean_json(wan_information)
    return cleaned_wan_information


def generate_VMANAGE_KB():
    try:
        wan_information = consolidate_wan_information()
        write_to_json(document=VMANAGE_KB_PATH, content=wan_information)
        log.info("vManage KB Update: Update Successful")
    except:
        log.info("vManage KB Update: Update Unuccessful")


if __name__ == '__main__':
    generate_VMANAGE_KB()
