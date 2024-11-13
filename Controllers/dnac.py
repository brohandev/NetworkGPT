# package import
import json
import logging
from requests import (
    post, Session,
    ConnectionError, HTTPError, Timeout
)
from urllib3.exceptions import InsecureRequestWarning
import warnings

# local file import
from Auxiliary.helper import (
    clean_json,
    epoch_datetime_converter,
    write_to_json
)
from Authentication.credentials import (
    DNA_CENTER_BASE_URL,
    DNA_CENTER_ENCODED_AUTH
)
from Storage.filepaths import (
    dnac_kb_filepath
)

logging.basicConfig()
log = logging.getLogger("DNAC_KB_Generation")
log.setLevel(logging.INFO)

warnings.filterwarnings("ignore", category=InsecureRequestWarning)


class DNAC:
    def __init__(self):
        self.session = self.authenticate()
        self.knowledge = self.initialize_base_knowledge()

    @staticmethod
    def authenticate():
        """
        Creates a Session object and authenticates with the DNAC node. A POST call is made to retrieve SDA X-Auth token.
        Upon successful retrieval, the Session object is updated with the X-Auth-Token field in the header and returned
        to the caller. Upon failure during the previous step, the program stops and exits.
        """
        session = Session()
        response = None
        dnac_x_auth_token = None

        payload = {}
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": "application/json"
        }

        try:
            response = post(DNA_CENTER_BASE_URL + "dna/system/api/v1/auth/token",
                            auth=DNA_CENTER_ENCODED_AUTH,
                            headers=headers,
                            data=payload,
                            verify=False)
            if response.ok:
                dnac_x_auth_token = response.json()["Token"]
            else:
                log.error("DNAC Authentication: Failed to retrieve SDA X-Auth Token.")
                response.raise_for_status()

        except HTTPError:
            if response.status_code == 401:
                log.error("DNAC Authentication: HTTP 401: Invalid credentials used.")
                exit()
            elif response.status_code == 404:
                log.error("DNAC Authentication: HTTP 404: Resource not found. Check URL validity.")
                exit()
        except ConnectionError:
            log.error("DNAC Authentication: Connection: Check network connectivity to DNAC node or check URL validity.")
            exit()
        except Timeout:
            log.error("DNAC Authentication: Timeout: Re-attempt authentication method.")
            exit()
        except Exception as e:
            log.error(f"DNAC Authentication: Unknown exception: Deeper troubleshooting required to fix {e}")
            exit()

        session.headers.update({
            "X-Auth-Token": dnac_x_auth_token
        })
        log.info("DNAC Authentication: Successful. Session headers updated.")

        return session

    def initialize_base_knowledge(self):
        with open(dnac_kb_filepath, "r") as file:
            dnac_base_kb = json.load(file)
        return dnac_base_kb

    def get_device_list(self, **device_fields):
        """
        Gets list of network devices based on filter criteria such as management IP address, mac address, hostname,
        etc. You can use the .* in any value to conduct a wildcard search. For example, to find all hostnames
        beginning with myhost in the IP address range 192.25.18.n, issue the following request: GET
        /dna/intent/api/v1/network-device?hostname=myhost.*&managementIpAddress=192.25.18..* If id parameter is
        provided with comma separated ids, it will return the list of network-devices for the given ids and ignores
        the other request parameters. You can also specify offset & limit to get the required list.

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
        DNAC_DEVICE_LIST_URL = DNA_CENTER_BASE_URL + "/dna/intent/api/v1/network-device"
        params = {}
        for field, value in device_fields.items():
            params[field] = value

        response = None
        try:
            response = self.session.get(DNAC_DEVICE_LIST_URL, params=params, verify=False)
            if response.ok:
                log.info("DNAC Get Device List: Successfully retrieved.")
                return response.json()["response"]
            else:
                response.raise_for_status()
        except HTTPError:
            if response.status_code == 401:
                log.error("DNAC Get Device List: HTTP 401: Invalid or expired credentials used.")
            elif response.status_code == 404:
                log.error("DNAC Get Device List: HTTP 404: Resource not found. Check URL validity.")
            log.error(f"DNAC Get Device List: Error Message: {response.json()['response']['detail']}")
            return []
        except ConnectionError:
            log.error("DNAC Get Device List: Connection: Check network connectivity to DNAC node.")
            return []
        except Timeout:
            log.error("DNAC Get Device List: Timeout: Re-attempt authentication method.")
            return []
        except Exception as e:
            log.error(f"DNAC Get Device List: Unknown exception: Deeper troubleshooting required to fix {e}")
            return []

    def get_hostname_by_device_id(self, device_id):
        """
        Queries SDA with device UUID to retrieve hostname of the switch
        :return: (str) hostname of the device
        """
        # query parameters
        DNAC_DEVICE = DNA_CENTER_BASE_URL + f"/dna/intent/api/v1/network-device/{device_id}"
        params = {}

        response = None
        try:
            response = self.session.get(DNAC_DEVICE, params=params, verify=False)
            response_dict = response.json()
            return response_dict["response"]["hostname"]
        except HTTPError:
            if response.status_code == 401:
                log.error("DNAC Get Hostname by Device ID: HTTP 401: Invalid or expired credentials used.")
            elif response.status_code == 404:
                log.error("DNAC Get Hostname by Device ID: HTTP 404: Resource not found. Check URL validity.")
            return ""
        except ConnectionError:
            log.error("DNAC Get Hostname by Device ID: Connection: Check network connectivity to DNAC node.")
            return ""
        except Timeout:
            log.error("DNAC Get Hostname by Device ID: Timeout: Re-attempt authentication method.")
            return ""
        except Exception as e:
            log.error(f"DNAC Get Hostname by Device ID: Unknown exception: Deeper troubleshooting required to fix {e} for device: {device_id}")
            return ""

    def get_dnac_nodes_list(self):
        """
        Gets config details of all DNAC nodes participating in SD-Access fabric.

        :param:
        1. None
        :return: (list[]) list containing device config represented as nested dict() objects
        Fields:
        """
        DNAC_NODES_CONFIG_URL = DNA_CENTER_BASE_URL + "/dna/intent/api/v1/nodes-config"
        params = {}

        response = None
        try:
            response = self.session.get(DNAC_NODES_CONFIG_URL, params=params, verify=False)
            if response.ok:
                log.info("DNAC Get DNAC Nodes List: Successfully retrieved.")
                return response.json()['response']['nodes']
            else:
                response.raise_for_status()
        except HTTPError:
            if response.status_code == 401:
                log.error("DNAC Get DNAC Nodes List: HTTP 401: Invalid or expired credentials used.")
            elif response.status_code == 404:
                log.error("DNAC Get DNAC Nodes: HTTP 404: Resource not found. Check URL validity.")
            log.error(f"DNAC Get DNAC Nodes List: Error Message: {response.json()['response']['detail']}")
            return []
        except ConnectionError:
            log.error("DNAC Get DNAC Nodes: Connection: Check network connectivity to DNAC node.")
            return []
        except Timeout:
            log.error("DNAC Get DNAC Nodes: Timeout: Re-attempt authentication method.")
            return []
        except Exception as e:
            log.error(f"DNAC Get DNAC Nodes: Unknown exception: Deeper troubleshooting required to fix {e}")
            return []

    def get_dnac_site_list(self):
        """
        Gets list of all fabric sites participating in SD-Access fabric.

        :param:
        1. None
        :return: (list[]) list containing site information represented as nested dict() objects
        Fields:
        """
        DNAC_SITES_URL = DNA_CENTER_BASE_URL + "/dna/intent/api/v1/site"
        params = {}

        response = None
        try:
            response = self.session.get(DNAC_SITES_URL, params=params, verify=False)
            if response.ok:
                log.info("DNAC Get DNAC Sites List: Successfully retrieved.")
                return response.json()['response']
            else:
                response.raise_for_status()
        except HTTPError:
            if response.status_code == 401:
                log.error("DNAC Get DNAC Sites List: HTTP 401: Invalid or expired credentials used.")
            elif response.status_code == 404:
                log.error("DNAC Get DNAC Sites: HTTP 404: Resource not found. Check URL validity.")
            log.error(f"DNAC Get DNAC Sites List: Error Message: {response.json()['response']['detail']}")
            return []
        except ConnectionError:
            log.error("DNAC Get DNAC Sites: Connection: Check network connectivity to DNAC node.")
            return []
        except Timeout:
            log.error("DNAC Get DNAC Sites: Timeout: Re-attempt authentication method.")
            return []
        except Exception as e:
            log.error(f"DNAC Get DNAC Sites: Unknown exception: Deeper troubleshooting required to fix {e}")
            return []

    def get_dnac_device_assigned_to_site_list(self):
        """
        Gets list of all device to site mappings participating in SD-Access fabric.

        :param:
        1. None
        :return: (list[]) list containing deivce-to-site information represented as nested dict() objects
        Fields:
        """
        DNAC_SITES_DEVICE_MAPPING_URL = DNA_CENTER_BASE_URL + "api/v2/data/lazy-load/com.cisco.dnac.model.ConnectivityDomain/1022c532-caa2-4301-b720-e9d67a602cc5/deviceInfo"
        params = {}

        response = None
        try:
            response = self.session.get(DNAC_SITES_DEVICE_MAPPING_URL, params=params, verify=False)
            if response.ok:
                log.info("DNAC Get DNAC Site Device Mapping List: Successfully retrieved.")
                return response.json()['response']
            else:
                response.raise_for_status()
        except HTTPError:
            if response.status_code == 401:
                log.error("DNAC Get DNAC Site Device Mapping List: HTTP 401: Invalid or expired credentials used.")
            elif response.status_code == 404:
                log.error("DNAC Get DNAC Sites: HTTP 404: Resource not found. Check URL validity.")
            log.error(f"DNAC Get DNAC Site Device Mapping List: Error Message: {response.json()['response']['detail']}")
            return []
        except ConnectionError:
            log.error("DNAC Get DNAC Site Device Mapping: Connection: Check network connectivity to DNAC node.")
            return []
        except Timeout:
            log.error("DNAC Get DNAC Site Device Mapping: Timeout: Re-attempt authentication method.")
            return []
        except Exception as e:
            log.error(
                f"DNAC Get DNAC Site Device Mapping: Unknown exception: Deeper troubleshooting required to fix {e}")
            return []

    def get_device_health_list(self, **device_fields):
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
        DNAC_DEVICE_HEALTH_LIST_URL = DNA_CENTER_BASE_URL + "/dna/intent/api/v1/device-health"
        params = {}
        for field, value in device_fields.items():
            params[field] = value

        response = None
        try:
            response = self.session.get(DNAC_DEVICE_HEALTH_LIST_URL, params=params, verify=False)
            if response.ok:
                log.info("DNAC Get Device Health List: Successfully retrieved.")
                return response.json()['response']
            else:
                response.raise_for_status()

        except HTTPError:
            if response.status_code == 401:
                log.error("DNAC Get Device Health List: HTTP 401: Invalid or expired credentials used.")
            elif response.status_code == 404:
                log.error("DNAC Get Device Health: HTTP 404: Resource not found. Check URL validity.")
            log.error(f"DNAC Get Device Health List: Error Message: {response.json()['response']['detail']}")
            return []
        except ConnectionError:
            log.error("DNAC Get Device Health: Connection: Check network connectivity to DNAC node.")
            return []
        except Timeout:
            log.error("DNAC Get Device Health: Timeout: Re-attempt authentication method.")
            return []
        except Exception as e:
            log.error(f"DNAC Get Device Health: Unknown exception: Deeper troubleshooting required to fix {e}")
            return []

    def get_device_interface_information_list(self, device_id):
        """
        Gets interface details of specified network device participating in SD-Access fabric.

        :param:
        1. (string) (required) deviceUuid (e.g., 826bc2f3-bf3f-465b-ad2e-e5701ff7a46c)
        :return: (list[]) list containing device interface information represented as nested dict() objects
        Fields:
        """
        DNAC_DEVICE_INTERFACE_INFO_URL = DNA_CENTER_BASE_URL + f"/dna/intent/api/v1/interface/network-device/{device_id}"
        params = {}

        response = None
        try:
            response = self.session.get(DNAC_DEVICE_INTERFACE_INFO_URL, params=params, verify=False)
            if response.ok:
                log.info("DNAC Get Device Interface Information List: Successfully retrieved.")
                return response.json()['response']
            else:
                response.raise_for_status()
        except HTTPError:
            if response.status_code == 401:
                log.error("DNAC Get Device Interface List: HTTP 401: Invalid or expired credentials used.")
            elif response.status_code == 404:
                log.error("DNAC Get Device Interface List: HTTP 404: Resource not found. Check URL validity.")
            log.error(f"DNAC Get Device Interface List: Error Message: {response.json()['response']['detail']}")
            return []
        except ConnectionError:
            log.error("DNAC Get Device Interface List: Connection: Check network connectivity to DNAC node.")
            return []
        except Timeout:
            log.error("DNAC Get Device Interface List: Timeout: Re-attempt authentication method.")
            return []
        except Exception as e:
            log.error(f"DNAC Get Device Interface List: Unknown exception: Deeper troubleshooting required to fix {e}")
            return []

    def get_device_module_information(self, device_id):
        """
        Gets details of hardware modules connected to specified device participating in SD-Access fabric.

        :param:
        1. (string) (required) deviceUuid (e.g., 826bc2f3-bf3f-465b-ad2e-e5701ff7a46c)
        :return: (dict{}) dict containing details of devices connected to specified device.

        Fields: name, description, serialNumber, partNumber
        """
        DNAC_DEVICE_MODULE_INFO_URL = DNA_CENTER_BASE_URL + f"/dna/intent/api/v1/network-device/module?deviceId={device_id}"
        params = {}

        response = None
        try:
            response = self.session.get(DNAC_DEVICE_MODULE_INFO_URL, params=params, verify=False)
            if response.ok:
                log.info("DNAC Get Device Module Information List: Successfully retrieved.")
                return response.json()['response']
            else:
                response.raise_for_status()
        except HTTPError:
            if response.status_code == 401:
                log.error("DNAC Get Device Module Information List: HTTP 401: Invalid or expired credentials used.")
            elif response.status_code == 404:
                log.error("DNAC Get Device Module Information List: HTTP 404: Resource not found. Check URL validity.")
            return []
        except ConnectionError:
            log.error("DNAC Get Device Module Information List: Connection: Check network connectivity to DNAC node.")
            return []
        except Timeout:
            log.error("DNAC Get Device Module Information List: Timeout: Re-attempt authentication method.")
            return []
        except Exception as e:
            log.error(
                f"DNAC Get Device Module Information List: Unknown exception: Deeper troubleshooting required to fix {e}")
            return []

    def get_device_neighbourship_information(self, device_id, interface_id):
        """
        Gets details of devices connected to specified device's specific interface participating in SD-Access fabric.

        :param:
        1. (string) (required) deviceUuid (e.g., 826bc2f3-bf3f-465b-ad2e-e5701ff7a46c)
        2. (string) (required) interfaceUuid (e.g., fadc2e17-aab7-4679-9a6b-103d08886187)
        :return: (dict{}) dict containing details of devices connected to specified device.

        Fields: capabilities:[], neighborDevice, neighborPort
        """
        DNAC_DEVICE_NEIGHBOURSHIP_INFO_URL = DNA_CENTER_BASE_URL + f"/dna/intent/api/v1/network-device/" \
                                                                   f"{device_id}/interface/{interface_id}/neighbor"
        params = {}

        response = None
        try:
            response = self.session.get(DNAC_DEVICE_NEIGHBOURSHIP_INFO_URL, params=params, verify=False)
            if response.ok:
                log.info("DNAC Get Device Neighbourship Information Dict: Successfully retrieved.")
                return response.json()['response']
            else:
                response.raise_for_status()
        except HTTPError:
            if response.status_code == 401:
                log.error("DNAC Get Device Neighbourship Dict: HTTP 401: Invalid or expired credentials used.")
            elif response.status_code == 404:
                log.error("DNAC Get Device Neighbourship Dict: HTTP 404: Resource not found. Check URL validity.")
            return []
        except ConnectionError:
            log.error("DNAC Get Device Neighbourship Dict: Connection: Check network connectivity to DNAC node.")
            return []
        except Timeout:
            log.error("DNAC Get Device Neighbourship Dict: Timeout: Re-attempt authentication method.")
            return []
        except Exception as e:
            log.error(f"DNAC Get Device Neighbourship Dict: Unknown exception: Deeper troubleshooting required to fix {e}")
            return []

    def consolidate_lan_device_information_list(self):
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
        initial_device_list = self.get_device_list()
        for device in initial_device_list:
            stripped_device_dict = {k: device[k] for k in device.keys() & {
                # 'family',
                'type',
                # 'softwareType',
                'softwareVersion',
                'serialNumber',
                'upTime',
                'hostname',
                'managementIpAddress',
                'reachabilityStatus',
                'role',
                'id'
            }}
            device_list.append(stripped_device_dict)

        # Retrieve health statistics of each device by hostname
        device_health_list = self.get_device_health_list()
        for device_detail_index in range(len(device_list)):
            for device_health_index in range(len(device_health_list)):
                if device_list[device_detail_index]["hostname"] == device_health_list[device_health_index]["name"]:
                    stripped_dict_obj = {k: device_health_list[device_health_index][k]
                                         for k in device_health_list[device_health_index].keys() & {
                                             'overallHealth',
                                             # 'issueCount',
                                             'interfaceLinkErrHealth',
                                             'cpuUlitilization',
                                             # 'cpuHealth',
                                             'memoryUtilization',
                                             # 'memoryUtilizationHealth',
                                             # 'interDeviceLinkAvailHealth'
                                         }}
                    device_list[device_detail_index].update(stripped_dict_obj)

        # Retrieve interface details of each device by device ID
        device_id_list = [obj_dict["id"] for obj_dict in device_list]
        clean_device_list = None
        for device_id in device_id_list:
            stripped_device_interfaces_list = []
            device_interfaces_list = self.get_device_interface_information_list(device_id=device_id)
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
                }}
                stripped_device_interfaces_list.append(stripped_dict_obj)

            # Retrieve neighbour details connected to each interface of each device
            interface_id_list = [obj_dict["id"] for obj_dict in stripped_device_interfaces_list]
            for interface_id in interface_id_list:
                neighbour_dict = self.get_device_neighbourship_information(device_id=device_id, interface_id=interface_id)
                interface_index = next(
                    i for i, item in enumerate(stripped_device_interfaces_list) if item["id"] == interface_id)
                if neighbour_dict is not None:
                    stripped_device_interfaces_list[interface_index]["neighbour"] = \
                        {k: neighbour_dict[k] for k in neighbour_dict.keys() & {
                            'neighborDevice',
                            'neighborPort'
                        }}
                else:
                    stripped_device_interfaces_list[interface_index]["neighbour"] = {}

            device_index = next(i for i, item in enumerate(device_list) if item["id"] == device_id)
            device_list[device_index]["interfaces"] = stripped_device_interfaces_list

            clean_device_list = [clean_json(dict_obj) for dict_obj in device_list]

        # Retrieve module information of each network device in SDA
        for device in clean_device_list:
            device_id = device["id"]
            module_info_list = [{
                "name": module["name"],
                "module_description": module["description"],
                "serial_number": module["serialNumber"],
                "part_number": module["partNumber"]
            } for module in self.get_device_module_information(device_id=device_id)]
            device["modules"] = module_info_list

        # Retrieve site information and append site field for each network device in SDA
        site_info_list = self.get_dnac_site_list()
        site_map = {}
        for site_info in site_info_list:
            site_map[site_info["id"]] = site_info["siteNameHierarchy"]
        for device in clean_device_list:
            for site_device_mapping in self.get_dnac_device_assigned_to_site_list():
                if site_device_mapping["networkDeviceId"] == device["id"]:
                    device["location"] = site_map[site_device_mapping["siteId"]]
                    break

        # Clean up the device fields
        final_device_list = [{
            "type": device["type"] if "type" in device.keys() else None,
            "serialNumber": device["serialNumber"] if "serialNumber" in device.keys() else None,
            "managementIPAddress": device["managementIpAddress"] if "managementIpAddress" in device.keys() else None,
            "softwareVersion": device["softwareVersion"] if "softwareVersion" in device.keys() else None,
            "hostname": device["hostname"] if "hostname" in device.keys() else None,
            "upTime": device["upTime"] if "upTime" in device.keys() else None,
            "reachability": device["reachabilityStatus"] if "reachabilityStatus" in device.keys() else None,
            "health": device["overallHealth"] if "overallHealth" in device.keys() else None,
            "location": device["location"] if "location" in device.keys() else None,
            "cpuUsage": device["cpuUlitilization"] if "cpuUlitilization" in device.keys() else None,
            "memoryUsage": device["memoryUtilization"] if "memoryUtilization" in device.keys() else None,
            "modules": device["modules"] if "modules" in device.keys() else [],
            "interfaces": [interface for interface in device["interfaces"] if interface["status"] == "up"]
            if "interfaces" in device.keys() else []
        } for device in clean_device_list]

        # Retrieve chassis details of each DNAC node in SDA
        dnac_node_list = self.get_dnac_nodes_list()
        for dnac_node in dnac_node_list:
            final_device_list.append(
                {
                    'hostname': dnac_node['platform']['product'],
                    'family': "DNA Center (DNAC)",
                    'ntp': dnac_node['ntp']['servers'],
                    'ipv4Addresses': [ip_dict_obj['inet']['host_ip'] for ip_dict_obj in dnac_node['network']
                                      if ip_dict_obj['inet']['host_ip']],
                    'vendor': dnac_node['platform']['vendor'],
                    'softwareVersion': '2.3.5.5',
                    'interfaces': []
                }
            )

        return final_device_list

    def get_network_issues(self):
        """
        Gets LAN-wide issues in SD-Access fabric.
        :return: list[] containing LAN-wide aggregated client health metrics represented as dict{} objects
        Fields:
        """
        DNAC_ISSUES_URL = DNA_CENTER_BASE_URL + "/dna/intent/api/v1/issues"
        params = {}

        response = None
        try:
            response = self.session.get(DNAC_ISSUES_URL, params=params, verify=False)
            if response.ok:
                log.info("DNAC Get Network Issues List: Successfully retrieved.")
                return response.json()['response']
            else:
                response.raise_for_status()

        except HTTPError:
            if response.status_code == 401:
                log.error("DNAC Get Network Issues List: HTTP 401: Invalid or expired credentials used.")
            elif response.status_code == 404:
                log.error("DNAC Get Network Issues: HTTP 404: Resource not found. Check URL validity.")
            log.error(f"DNAC Get Network Issues List: Error Message: {response.json()['response']['detail']}")
            return []
        except ConnectionError:
            log.error("DNAC Get Network Issues: Connection: Check network connectivity to DNAC node.")
            return []
        except Timeout:
            log.error("DNAC Get Network Issues: Timeout: Re-attempt authentication method.")
            return []
        except Exception as e:
            log.error(f"DNAC Get Network Issues: Unknown exception: Deeper troubleshooting required to fix {e}")
            return []

    def consolidate_lan_issues(self):
        """
        1. Retrieve LAN-wide issues list
        2. Clean fields and consolidate issues into 1 overall health dict
        :return: dict{} containing LAN-wide health metrics
        """
        issues = []
        for issue in self.get_network_issues():
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

            stripped_issue_dict['deviceName'] = self.get_hostname_by_device_id(stripped_issue_dict['deviceId'])
            del stripped_issue_dict['deviceId']

            issues.append(stripped_issue_dict)

        return issues if issues else ["No Issues/Events/Problems in the LAN"]

    def get_clients_list(self):
        """
        Gets clients connected/disconnected in SD-Access fabric.
        :return: list[] containing LAN-wide client health metrics represented as dict{} objects
        Fields:
        """
        DNAC_CLIENTS_URL = f"{DNA_CENTER_BASE_URL}/api/assurance/v1/host"
        self.session.headers.update({'Content-Type': 'application/json'})
        response = None
        try:
            response = self.session.post(url=DNAC_CLIENTS_URL, data=json.dumps({}), verify=False)
            if response.ok:
                log.info("DNAC Get Network Clients List: Successfully retrieved.")
                return response.json()['response']
            else:
                response.raise_for_status()

        except HTTPError:
            if response.status_code == 401:
                log.error("DNAC Get Network Clients List: HTTP 401: Invalid or expired credentials used.")
            elif response.status_code == 404:
                log.error("DNAC Get Network Clients: HTTP 404: Resource not found. Check URL validity.")
            return []
        except ConnectionError:
            log.error("DNAC Get Network Clients: Connection: Check network connectivity to DNAC node.")
            return []
        except Timeout:
            log.error("DNAC Get Network Clients: Timeout: Re-attempt authentication method.")
            return []
        except Exception as e:
            log.error(f"DNAC Get Network Clients: Unknown exception: Deeper troubleshooting required to fix {e}")
            return []

    def consolidate_lan_clients(self):
        """
        1. Retrieve LAN-wide clients list
        2. Clean fields and consolidate clients into 1 overall clients dict
        :return: dict{} containing LAN-wide client information
        """
        clients = []
        for client in self.get_clients_list():
            clients.append({
                "authentication": client["authType"],
                "connected_device_hostname": client["connectedDevice"][0]["name"],
                "connected_device_ip": client["connectedDevice"][0]["mgmtIp"],
                "status": client["connectionStatus"],
                "data_rate": client["dataRate"],
                "data_usage": str(client["usage"]) + "B",
                "health": [score["score"] for score in client["healthScore"] if score["healthType"] == "OVERALL"][0],
                "client_id": client["userId"],
                "client_ip": client["hostIpV4"],
                "client_mac": client["hostMac"],
                "client_hostname": client["hostName"],
                "client_OS": client["hostOs"],
                "client_type": client["hostType"],
                "rssi": client["avgRssi"],
                "snr": client["avgSnr"],
                "channel": client["channel"],
                "l2_VN": client["l2VirtualNetwork"],
                "l3_VN": client["l3VirtualNetwork"],
                "last_updated": epoch_datetime_converter(client["lastUpdated"] / 1000),
                "onboarding_time": epoch_datetime_converter(client["onboardingTime"] / 1000),
                "location": client["location"],
                "roaming_time": str(client["maxRoamingDuration"]) + "min" if client["maxRoamingDuration"] else 0,
                "vlan": client["vlanId"],
                "VN_ID": client["vnid"],
                "WLC_name": client["wlcName"]
            })
        return clients

    def generate_lan_kb(self):
        try:
            LAN_DEVICES = self.consolidate_lan_device_information_list()
            LAN_INTERFACES = [{
                "hostname": device["hostname"],
                "interfaces": device["interfaces"]
            } for device in self.consolidate_lan_device_information_list()]
            LAN_ISSUES = self.consolidate_lan_issues()
            LAN_CLIENTS = self.consolidate_lan_clients()

            for client in LAN_CLIENTS:
                connected_device_hostname = client["connected_device_hostname"]
                for device in LAN_DEVICES:
                    if device["hostname"] == connected_device_hostname:
                        if "client_count" not in device.keys():
                            device["client_count"] = 1
                        else:
                            device["client_count"] += 1

            self.knowledge = {
                "LAN_DEVICES": LAN_DEVICES,
                "LAN_INTERFACES": LAN_INTERFACES,
                "LAN_ISSUES": LAN_ISSUES,
                "LAN_CLIENTS": LAN_CLIENTS
            }
            log.info("DNAC KB Update: Update Successful")
        except Exception as e:
            log.error(f"DNAC KB Update: Update Unsuccessful. Exception hit: {e}")

    def store_lan_kb(self):
        try:
            self.generate_lan_kb()
            write_to_json(
                document=dnac_kb_filepath,
                content=self.knowledge
            )
            log.info("DNAC KB Storage: Storage Successful")
        except Exception as e:
            log.error(f"DNAC KB Storage: Storage Unsuccessful. Exception hit: {e}")


if __name__ == '__main__':
    dnac = DNAC()
    # pp(dnac.get_network_issues())
    dnac.store_lan_kb()
