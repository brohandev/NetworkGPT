# package import
import json
import logging
from requests import (
    get, post, Session,
    ConnectionError, HTTPError, Timeout
)
from urllib3.exceptions import InsecureRequestWarning
import warnings

# local file import
from Auxiliary.helper import (
    epoch_datetime_converter,
    write_to_json
)
from Authentication.credentials import (
    VMANAGE_BASE_URL,
    # VMANAGE_API_URL = "/dataservice"
    # VMANAGE_AUTH_SESSION_URL = VMANAGE_BASE_URL + '/j_security_check'
    # VMANAGE_AUTH_TOKEN_URL = VMANAGE_BASE_URL + '/dataservice/client/token'
    VMANAGE_USERNAME,
    VMANAGE_PASSWORD
)
from Storage.filepaths import (
    vmanage_kb_filepath
)

logging.basicConfig()
log = logging.getLogger("vManage_KB_Generation")
log.setLevel(logging.INFO)

warnings.filterwarnings("ignore", category=InsecureRequestWarning)


class vMANAGE:
    def __init__(self):
        self.session = self.authenticate()
        self.knowledge = None
        # self.knowledge = self.initialize_base_knowledge()

    @staticmethod
    def authenticate():
        """
        Creates a Session object and authenticates with the vManage node. 2 separate GET requests are made to retrieve
        Session_ID and X-XRF Token. Upon successful retrieval, the Session object is updated with the 2 fields in the
        header and returned to the caller. Upon failure during any of the previous steps, the program stops and exits.
        """
        session = Session()
        response = None
        vmanage_session_id = None
        vmanage_x_xsrf_token = None

        payload = {
            "j_username": VMANAGE_USERNAME,
            "j_password": VMANAGE_PASSWORD
        }

        try:
            # retrieve vManage session ID
            response = post(VMANAGE_BASE_URL + "/j_security_check",
                            data=payload,
                            verify=False)
            if response.ok:
                cookies = response.headers["Set-Cookie"]
                vmanage_session_id = cookies.split(";")[0]
            else:
                log.error("vManage Authentication: Failed to retrieve vManage session ID.")
                response.raise_for_status()

            # retrieve vManage session token
            response = get(url=VMANAGE_BASE_URL + '/dataservice/client/token',
                           headers={"Cookie": vmanage_session_id},
                           verify=False)
            if response.ok:
                vmanage_x_xsrf_token = response.text
            else:
                log.error("vManage Authentication: Failed to retrieve vManage session token")
                response.raise_for_status()

            # populate vManage session headers for persistent usage
            if vmanage_x_xsrf_token is not None:
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

        except HTTPError:
            if response.status_code == 401:
                log.error("vManage Authentication: HTTP 401: Invalid credentials used.")
                exit()
            elif response.status_code == 404:
                log.error("vManage Authentication: HTTP 404: Resource not found. Check URL validity.")
                exit()
        except ConnectionError:
            log.error("vManage Authentication: Connection: Check network connectivity to DNAC node or check URL validity.")
            exit()
        except Timeout:
            log.error("vManage Authentication: Timeout: Re-attempt authentication method.")
            exit()
        except Exception as e:
            log.error(f"vManage Authentication: Unknown exception: Deeper troubleshooting required to fix {e}")
            exit()

    def initialize_base_knowledge(self):
        with open(vmanage_kb_filepath, "r") as file:
            vmanage_base_kb = json.load(file)
        return vmanage_base_kb

    def get_device_list(self):
        """
        Retrieve and return network devices list. Returns information about each device that is part of the fabric.
        :param: None
        :return: (list[]) list containing SDWAN devices represented as dict() objects
        """
        VMANAGE_DEVICE_LIST_URL = VMANAGE_BASE_URL + "/dataservice/device"
        response = None
        try:
            response = self.session.get(VMANAGE_DEVICE_LIST_URL, verify=False)
            if response.ok:
                log.info("vManage Get Device List: Successfully retrieved.")
                return response.json()['data']
            else:
                response.raise_for_status()
        except HTTPError:
            if response.status_code == 401:
                log.error("vManage Get Device List: HTTP 401: Invalid or expired credentials used.")
            elif response.status_code == 404:
                log.error("vManage Get Device List: HTTP 404: Resource not found. Check URL validity.")
            log.error(f"vManage Get Device List: Error Message: {response.json()['response']['detail']}")
            return []
        except ConnectionError:
            log.error("vManage Get Device List: Connection: Check network connectivity to DNAC node.")
            return []
        except Timeout:
            log.error("vManage Get Device List: Timeout: Re-attempt authentication method.")
            return []
        except Exception as e:
            log.error(f"vManage Get Device List: Unknown exception: Deeper troubleshooting required to fix {e}")
            return []

    def get_device_interface_info(self, system_ip):
        """
        Retrieve and return information about interface status of specified network device in SD-WAN fabric
        :param: (string) system_ip
        :return: (list[]) list containing interface information of each SDWAN device represented as a dict() object
        """
        # query parameters
        VMANAGE_DEVICE_INTERFACE_URL = VMANAGE_BASE_URL + f"/dataservice/device/interface/synced?deviceId={system_ip}"

        response = None
        try:
            response = self.session.get(VMANAGE_DEVICE_INTERFACE_URL, verify=False)
            if response.ok:
                log.info("vManage Get Device Interface List: Successfully retrieved.")
                return response.json()['data']
        except HTTPError:
            if response.status_code == 401:
                log.error("vManage Get Device Interface List: HTTP 401: Invalid or expired credentials used.")
            elif response.status_code == 404:
                log.error("vManage Get Device Interface List: HTTP 404: Resource not found. Check URL validity.")
            return []
        except ConnectionError:
            log.error("vManage Get Device Interface List: Connection: Check network connectivity to DNAC node.")
            return []
        except Timeout:
            log.error("vManage Get Device Interface List: Timeout: Re-attempt authentication method.")
            return []
        except Exception as e:
            log.error(f"vManage Get Device Interface List: Unknown exception: Deeper troubleshooting required to fix "
                      f"{e} for device: {system_ip}")
            return []

    def get_device_status(self, system_ip):
        """
        Retrieve and return information about System status of specified network device in SD-WAN fabric
        :param: (string) system_ip
        :return: (list[]) list containing status information of each SDWAN device represented as a dict() object
        """
        # query parameters
        VMANAGE_DEVICE_INTERFACE_URL = VMANAGE_BASE_URL + f"/dataservice/device/system/status?deviceId={system_ip}"

        response = None
        try:
            response = self.session.get(VMANAGE_DEVICE_INTERFACE_URL, verify=False)
            if response.ok:
                log.info("vManage Get Device Interface List: Successfully retrieved.")
                return response.json()['data']
        except HTTPError:
            if response.status_code == 401:
                log.error("vManage Get Device Interface List: HTTP 401: Invalid or expired credentials used.")
            elif response.status_code == 404:
                log.error("vManage Get Device Interface List: HTTP 404: Resource not found. Check URL validity.")
            return []
        except ConnectionError:
            log.error("vManage Get Device Interface List: Connection: Check network connectivity to DNAC node.")
            return []
        except Timeout:
            log.error("vManage Get Device Interface List: Timeout: Re-attempt authentication method.")
            return []
        except Exception as e:
            log.error(f"vManage Get Device Interface List: Unknown exception: Deeper troubleshooting required to fix "
                      f"{e} for device: {system_ip}")
            return []

    def get_alarms(self, **device_fields):
        """
        Retrieve and return WAN alarms list. Returns information about each alarm and the devices it affects.
        :param: None
        :return: (list[]) list containing SDWAN alarms/problems represented as dict() objects
        """
        VMANAGE_ALARMS_LIST_URL = VMANAGE_BASE_URL + "/dataservice/alarms"
        response = None
        try:
            response = self.session.get(VMANAGE_ALARMS_LIST_URL, verify=False)
            if response.ok:
                log.info("vManage Get Alarms List: Successfully retrieved.")
                return response.json()['data']
            else:
                response.raise_for_status()
        except HTTPError:
            if response.status_code == 401:
                log.error("vManage Get Alarms List: HTTP 401: Invalid or expired credentials used.")
            elif response.status_code == 404:
                log.error("vManage Get Alarms List: HTTP 404: Resource not found. Check URL validity.")
            return []
        except ConnectionError:
            log.error("vManage Get Alarms List: Connection: Check network connectivity to DNAC node.")
            return []
        except Timeout:
            log.error("vManage Get Alarms List: Timeout: Re-attempt authentication method.")
            return []
        except Exception as e:
            log.error(f"vManage Get Alarms List: Unknown exception: Deeper troubleshooting required to fix {e}")
            return []

    def consolidate_wan_device_information(self):
        """
        1. Retrieve WAN device list and device-associated fields
        2. Retrieve interface information per WAN device by system IP, append inerface information as a list of dict objects
        :return: (list[]) list containing device and interface information represented as nested dict() objects
        """
        # Retrieve device details of each device
        initial_device_list = self.get_device_list()
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
            device_status = self.get_device_status(system_ip=stripped_device_dict['system-ip'])[0]
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
            device_interfaces_list = self.get_device_interface_info(system_ip=stripped_device_dict['system-ip'])
            device_interfaces_list = [{k: interface[k] for k in interface.keys() & {
                'if-admin-status',
                'vpn-id',
                'mtu',
                'ip-address',
                'ipv4-subnet-mask',
                'speed-mbps',
                'hwaddr'
            }
                                       } for interface in device_interfaces_list]
            stripped_device_dict["interfaces"] = [interface for interface in device_interfaces_list
                                                  if interface['if-admin-status'] == 'Up']

            device_list.append(stripped_device_dict)

        return device_list

    def consolidate_wan_issues(self):
        # Retrieve issue details of each issue
        issues_list = self.get_alarms()
        issues_list = [{k: issue[k] for k in issue.keys() & {
            'active',
            'system_ip',
            'id',
            'message',
            'severity',
            'severity_number',
            'entry_time'
        }
                        } for issue in issues_list]

        issues_list = [{
            "status": "active" if issue["active"] else "inactive",
            "severity": issue["severity"],
            "system_ip": issue["system_ip"],
            "error_message": issue["message"],
            "time": epoch_datetime_converter(issue["entry_time"] / 1000)
        } for issue in issues_list if issue['active'] is True]

        return issues_list if issues_list else ["No Issues/Events/Problems in the WAN"]

    def generate_wan_kb(self):
        try:
            WAN_DEVICES = self.consolidate_wan_device_information()
            WAN_INTERFACES = [{
                "hostname": device["host-name"],
                "interfaces": device["interfaces"]
            } for device in WAN_DEVICES]
            WAN_ISSUES = self.consolidate_wan_issues()

            self.knowledge = {
                "WAN_DEVICES": WAN_DEVICES,
                "WAN_INTERFACES": WAN_INTERFACES,
                "WAN_ISSUES": WAN_ISSUES
            }
            log.info("vManage KB Update: Update Successful")
        except Exception as e:
            log.error(f"vManage KB Update: Update Unsuccessful. Exception hit: {e}")

    def store_wan_kb(self):
        try:
            self.generate_wan_kb()
            write_to_json(
                document=vmanage_kb_filepath,
                content=self.knowledge
            )
            log.info("vManage KB Storage: Storage Successful")
        except Exception as e:
            log.error(f"vManage KB Storage: Storage Unsuccessful. Exception hit: {e}")


if __name__ == '__main__':
    vManage = vMANAGE()
    # pp(vManage.consolidate_wan_device_information())
    # pp(vManage.get_device_interface_info(system_ip="10.10.10.1"))
    vManage.store_wan_kb()
