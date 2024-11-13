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
    epoch_datetime_converter,
    write_to_json
)
from Authentication.credentials import (
    KNOX_AUTH_URL,
    KNOX_BASE_URL,
    KNOX_CLIENT_ID,
    KNOX_CLIENT_SECRET
)
from Storage.filepaths import (
    knox_kb_filepath
)

logging.basicConfig()
log = logging.getLogger("KNOX_KB_Generation")
log.setLevel(logging.INFO)

warnings.filterwarnings("ignore", category=InsecureRequestWarning)


class Knox:
    def __init__(self):
        self.session = self.authenticate()
        self.knowledge = self.initialize_base_knowledge()

    @staticmethod
    def authenticate():
        """
        Creates a Session object and authenticates with the Knox server. A POST call is made to retrieve Knox access
        token. Upon successful retrieval, the Session object is updated with the bearer access token and returned to
        the caller. Upon failure during the previous step, the program stops and exits.
        """
        session = Session()
        response = None
        access_token = None

        payload = {}
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }

        try:
            response = post(KNOX_AUTH_URL + f"grant_type=client_credentials"
                                            f"&client_id={KNOX_CLIENT_ID}"
                                            f"&client_secret={KNOX_CLIENT_SECRET}",
                            headers=headers,
                            data=payload)
            if response.ok:
                access_token = response.json()["access_token"]
            else:
                log.error("Knox Authentication: Failed to retrieve access token.")
                response.raise_for_status()

        except HTTPError:
            if response.status_code == 401:
                log.error("Knox Authentication: HTTP 401: Invalid credentials used.")
                exit()
            elif response.status_code == 404:
                log.error("Knox Authentication: HTTP 404: Resource not found. Check URL validity.")
                exit()
        except ConnectionError:
            log.error("Knox Authentication: Connection: Check network connectivity to Knox server or check URL "
                      "validity.")
            exit()
        except Timeout:
            log.error("Knox Authentication: Timeout: Re-attempt authentication method.")
            exit()
        except Exception as e:
            log.error(f"Knox Authentication: Unknown exception: Deeper troubleshooting required to fix {e}")
            exit()

        session.headers.update({
            "Authorization": f"Bearer {access_token}"
        })
        log.info("Knox Authentication: Successful. Session headers updated.")

        return session

    def initialize_base_knowledge(self):
        with open(knox_kb_filepath, "r") as file:
            knox_base_kb = json.load(file)
        return knox_base_kb

    def get_device_list(self):
        """
        Retrieve and return Samsung device list. Returns information about each device that is part of the tenant.
        :param: None
        :return: (list[]) list containing Samsung devices represented as dict() objects
        """
        KNOX_DEVICE_LIST_URL = KNOX_BASE_URL + "/device/selectDeviceList"
        response = None
        try:
            response = self.session.post(url=KNOX_DEVICE_LIST_URL)
            if response.ok:
                log.info("Knox Get Device List: Successfully retrieved.")
                return response.json()['resultValue']['deviceList']
            else:
                response.raise_for_status()
        except HTTPError:
            if response.status_code == 401:
                log.error("Knox Get Device List: HTTP 401: Invalid or expired credentials used.")
            elif response.status_code == 404:
                log.error("Knox Get Device List: HTTP 404: Resource not found. Check URL validity.")
            return []
        except ConnectionError:
            log.error("Knox Get Device List: Connection: Check network connectivity to DNAC node.")
            return []
        except Timeout:
            log.error("Knox Get Device List: Timeout: Re-attempt authentication method.")
            return []
        except Exception as e:
            log.error(f"Knox Get Device List: Unknown exception: Deeper troubleshooting required to fix {e}")
            return []

    def get_device_info(self, device_id) -> dict:
        """
        Retrieve and return detailed device information.
        :param: None
        :return: (dict{}) dict containing device information
        """
        KNOX_DEVICE_LIST_URL = KNOX_BASE_URL + "/device/selectDeviceInfo"
        response = None
        try:
            response = self.session.post(url=KNOX_DEVICE_LIST_URL,
                                         data=f"deviceId={device_id}")
            if response.ok and response.json()["resultMessage"] == "No Error":
                log.info("Knox Get Device Information: Successfully retrieved.")
                return response.json()['resultValue']
            else:
                response.raise_for_status()
        except HTTPError:
            if response.status_code == 401:
                log.error("Knox Get Device Information: HTTP 401: Invalid or expired credentials used.")
            elif response.status_code == 404:
                log.error("Knox Get Device Information: HTTP 404: Resource not found. Check URL validity.")
            return {}
        except ConnectionError:
            log.error("Knox Get Device Information: Connection: Check network connectivity to Knox server.")
            return {}
        except Timeout:
            log.error("Knox Get Device Information: Timeout: Re-attempt authentication method.")
            return {}
        except Exception as e:
            log.error(f"Knox Get Device Information: Unknown exception: Deeper troubleshooting required to fix {e}")
            return {}

    def get_application_list(self, device_id):
        """
        Retrieve and return list of 3rd party installed applications.
        :param: None
        :return: (list[]) list containing applications represented as dict() objects
        """
        KNOX_DEVICE_LIST_URL = KNOX_BASE_URL + "/device/selectDeviceAppList"
        response = None
        try:
            response = self.session.post(url=KNOX_DEVICE_LIST_URL,
                                         data=f"deviceId={device_id}")
            if response.ok and response.json()["resultMessage"] == "No Error":
                log.info("Knox Get Application List: Successfully retrieved.")
                return [app for app in response.json()['resultValue']['appList'] if app["systemApp"] == "ThirdPartyApp"]
            else:
                response.raise_for_status()
        except HTTPError:
            if response.status_code == 401:
                log.error("Knox Get Application List: HTTP 401: Invalid or expired credentials used.")
            elif response.status_code == 404:
                log.error("Knox Get Application List: HTTP 404: Resource not found. Check URL validity.")
            return []
        except ConnectionError:
            log.error("Knox Get Application List: Connection: Check network connectivity to Knox server.")
            return []
        except Timeout:
            log.error("Knox Get Application List: Timeout: Re-attempt authentication method.")
            return []
        except Exception as e:
            log.error(f"Knox Get Application List: Unknown exception: Deeper troubleshooting required to fix {e}")
            return []

    def consolidate_device_information_list(self):
        """
        1. Retrieve Samsung device list and fundamental device-associated fields
        2. Use device ID to retrieve detailed information per device
        3. Use device ID to retrieve list of installed 3rd party applications
        4. Append information and application information to corresponding device list info
        :return: (list[]) list containing device information represented as nested dict() objects
        """
        device_list = []

        # 1. Retrieve fundamental details of each enrolled device in Samsung Knox
        initial_device_list = self.get_device_list()
        for device in initial_device_list:
            # 2. Use device ID to retrieve detailed information per device
            raw_device_info = self.get_device_info(device_id=device["deviceId"])

            # 3. Use device ID to retrieve list of installed applications per device
            raw_app_list = self.get_application_list(device_id=device["deviceId"])
            cleaned_app_list = []
            for app in raw_app_list:
                cleaned_app_list.append({
                    "name": app["appName"],
                    "version": app["versionName"],
                    "binary_size": app["binarySize"],
                    "managed": True if app["isManaged"] == "Yes" else False,
                    "installed_datetime": epoch_datetime_converter(epoch_time=app["installed"]["time"]/1000)
                })

            # 4. Construct final device object and populate consolidated device_list
            device_dict = {
                # fundamental fields
                "device_id": device["deviceId"],
                "mobile_id": device["mobileId"],
                "lock_status": device["isDeviceLock"] if len(device["isDeviceLock"]) else "Unknown",
                "model": device["deviceModelKind"],
                "serial_number": device["serialNumber"],
                "username": device["userName"],
                "last_connected_time": epoch_datetime_converter(epoch_time=device["lastConnectionDate"]["time"]/1000),
                "email": device["email"],
                # detailed fields
                "organization": raw_device_info["orgName"],
                "license_end_date": raw_device_info["assignedLicenseEndDate"],
                "battery": raw_device_info["battery"],
                "ip_address": raw_device_info["wifiIpAddress"],
                "roaming": False if raw_device_info["isRoaming"] == "NotRoaming" else True,
                "contain_malware": False if raw_device_info["isContainMalware"] == "N" else True,
                "sim_card": raw_device_info["simStatus"],
                # application fields
                "applications": cleaned_app_list,
            }

            device_list.append(device_dict)

        return device_list

    def generate_knox_kb(self):
        try:
            self.knowledge = {
                "SAMSUNG_DEVICES": self.consolidate_device_information_list()
            }
            log.info("Knox KB Update: Update Successful")
        except Exception as e:
            log.error(f"Knox KB Update: Update Unsuccessful. Exception hit: {e}")

    def store_knox_kb(self):
        try:
            self.generate_knox_kb()
            write_to_json(
                document=knox_kb_filepath,
                content=self.knowledge
            )
            log.info("Knox KB Storage: Storage Successful")
        except Exception as e:
            log.error(f"Knox KB Storage: Storage Unsuccessful. Exception hit: {e}")


if __name__ == '__main__':
    knox = Knox()
    # pp(knox.get_device_list())
    # pp(knox.get_application_list(device_id="66243deb082343e689512115228215f2"))
    # pp(knox.consolidate_device_information_list())
    knox.store_knox_kb()
