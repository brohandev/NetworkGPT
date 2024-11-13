# package import
import json
import logging
from pprint import pprint as pp
from requests import (
    post, Session,
    ConnectionError, HTTPError, Timeout
)
from urllib3.exceptions import InsecureRequestWarning
import warnings

# local file import
from Auxiliary.helper import (
    deduplicate_list,
    python_datetime_converter,
    write_to_json
)
from Authentication.credentials import (
    SNA_BASE_URL,
    SNA_USERNAME,
    SNA_PASSWORD
)
from Storage.filepaths import (
    snam_kb_filepath
)

logging.basicConfig()
log = logging.getLogger("SNAM_KB_Generation")
log.setLevel(logging.INFO)

warnings.filterwarnings("ignore", category=InsecureRequestWarning)


class SNAM:
    def __init__(self):
        self.session = self.authenticate()
        self.tenant_id = 301
        self.knowledge = None
        # self.knowledge = self.initialize_base_knowledge()

    @staticmethod
    def authenticate():
        """
        Creates a Session object and authenticates with the SNA Manager node. A single POST request is made to retrieve
        XSRF Token. Upon successful retrieval, the Session object is updated with the "X-XSRF-TOKEN" field in the
        header and returned to the caller. Upon failure during any of the previous steps, the program stops and exits.
        """
        session = Session()

        login_request_data = {
            "username": SNA_USERNAME,
            "password": SNA_PASSWORD
        }

        response = post(url=SNA_BASE_URL + "/token/v2/authenticate",
                        verify=False,
                        data=login_request_data)

        try:
            if response.ok:
                # Set XSRF token for future requests
                for cookie in response.cookies:
                    if cookie.name == 'XSRF-TOKEN':
                        XSRF_TOKEN = cookie.value
                        session.headers.update({'X-XSRF-TOKEN': XSRF_TOKEN})
                        break
                log.info('SNAM Authentication: Successful.')
                return session

            else:
                response.raise_for_status()

        except HTTPError:
            if response.status_code == 400:
                log.error('SNAM Authentication: HTTP Status 400: Either missing authentication token or invalid URL '
                          'used.')
                exit()
            if response.status_code == 401:
                log.error('SNAM Authentication: HTTP Status 401: Expired or invalid authentication token; client '
                          'should re-authenticate')
                exit()
            if response.status_code == 403:
                log.error('SNAM Authentication: HTTP Status 403: Unauthorized access to Stealthwatch data. Please '
                          'enable your appropriate AnyConnect VPN or adjust admin permissions.')
                exit()
            if response.status_code == 404:
                log.error('SNAM Authentication: HTTP Status 404: Resource not found, invalid or inaccessible path '
                          'parameters.')
                exit()
        except ConnectionError:
            log.error("SNAM Authentication: Connection: Check network connectivity to SNAM node or check URL validity.")
            exit()
        except Timeout:
            log.error("SNAM Authentication: Timeout: Re-attempt authentication method.")
            exit()
        except Exception as e:
            log.error(f"SNAM Authentication: Unknown exception: Deeper troubleshooting required to fix {e}")
            exit()

    def test_snam(self):
        try:
            pp(self.session.headers)

            response = self.session.get(
                url=SNA_BASE_URL + f'/smc-configuration/rest/v1/tenants/{self.tenant_id}/tags/',
                verify=False
            )
            if response.ok:
                tag_list = json.loads(response.content)["data"]
                for tag in tag_list:
                    print("Tag ID = {}; Tag Name = {}".format(tag['id'], tag['name']))
            else:
                response.raise_for_status()
        except Exception as e:
            pp(f"Error: {e}")

    def initialize_base_knowledge(self):
        with open(snam_kb_filepath, "r") as file:
            snam_base_kb = json.load(file)
        return snam_base_kb

    def get_sna_host_tag_mapping(self):
        mapping = []
        response = None

        # Retrieve Internal Host Tags
        try:
            response = self.session.get(
                url=SNA_BASE_URL + f"/smc-configuration/rest/v1/tenants/301/tags",
                verify=False
            )
            if response.ok:
                log.info("SNAM Get SNA Internal Host Tag Mapping: Successful.")
                pp(response.text)
                # mapping.extend(response.json()['data'])
            else:
                log.error("SNAM Get SNA Internal Host Tag Mapping: Unsuccessful.")
                response.raise_for_status()
        except HTTPError:
            if response.status_code == 400:
                log.error("SNAM Get SNA Internal Host Tag Mapping:: HTTP 400.")
                pp(response.json())
                exit()
            elif response.status_code == 401:
                log.error("SNAM Get SNA Internal Host Tag Mapping:: HTTP 401: Invalid credentials used.")
                exit()
            elif response.status_code == 404:
                log.error("SNAM Get SNA Internal Host Tag Mapping:: HTTP 404: Resource not found. Check URL validity.")
                exit()
        except ConnectionError:
            log.error(
                "SNAM Get SNA Internal Host Tag Mapping:: Connection: Check network connectivity to SNAM node or check "
                "URL validity.")
            exit()
        except Timeout:
            log.error("SNAM Get SNA Internal Host Tag Mapping:: Timeout: Re-attempt authentication method.")
            exit()
        except Exception as e:
            log.error(
                f"SNAM Get SNA Internal Host Tag Mapping:: Unknown exception: Deeper troubleshooting required to fix {e}")
            exit()

        # Retrieve External Host Tags
        response = None
        try:
            response = self.session.get(
                url=SNA_BASE_URL + f"/sw-reporting/rest/v1/tenants/301/tags",
                verify=False
            )
            if response.ok:
                log.info("SNAM Get SNA External Host Tag Mapping: Successful.")
                mapping.extend(response.json()['data'])
            else:
                log.error("SNAM Get SNA External Host Tag Mapping: Unsuccessful.")
                response.raise_for_status()
        except HTTPError:
            if response.status_code == 401:
                log.error("SNAM Get SNA External Host Tag Mapping:: HTTP 401: Invalid credentials used.")
                exit()
            elif response.status_code == 404:
                log.error(
                    "SNAM Get SNA External Host Tag Mapping:: HTTP 404: Resource not found. Check URL validity.")
                exit()
        except ConnectionError:
            log.error(
                "SNAM Get SNA External Host Tag Mapping:: Connection: Check network connectivity to SNAM node or check URL validity.")
            exit()
        except Timeout:
            log.error("SNAM Get SNA External Host Tag Mapping:: Timeout: Re-attempt authentication method.")
            exit()
        except Exception as e:
            log.error(
                f"SNAM Get SNA External Host Tag Mapping:: Unknown exception: Deeper troubleshooting required to fix {e}")
            exit()

        # Retrieve Custom Host Tags
        response = None
        try:
            response = self.session.get(
                url=SNA_BASE_URL + f"/sw-reporting/rest/v1/tenants/{self.tenant_id}/customHosts/tags",
                verify=False)
            if response.ok:
                log.info("SNAM Get SNA Custom Host Tags: Successful.")
                mapping.extend(response.json()['data'])
                log.info("SNAM Get SNA Host Tag Mapping: Overall Successful.")
                return dict([(item["id"], item["displayName"]) for item in mapping])
            else:
                log.error("SNAM Get SNA Custom Host Tags: Unsuccessful.")
                response.raise_for_status()

        except HTTPError:
            if response.status_code == 401:
                log.error("SNAM Get SNA Custom Host Tags:: HTTP 401: Invalid credentials used.")
                exit()
            elif response.status_code == 404:
                log.error(
                    "SNAM Get SNA Custom Host Tags:: HTTP 404: Resource not found. Check URL validity.")
                exit()
        except ConnectionError:
            log.error(
                "SNAM Get SNA Custom Host Tags:: Connection: Check network connectivity to SNAM node or check URL validity.")
            exit()
        except Timeout:
            log.error("SNAM Get SNA Custom Host Tags:: Timeout: Re-attempt authentication method.")
            exit()
        except Exception as e:
            log.error(
                f"SNAM Get SNA Custom Host Tags:: Unknown exception: Deeper troubleshooting required to fix {e}")
            exit()

    def get_sna_events(self):
        # Retrieve Security Events
        response = None
        try:
            response = self.session.get(
                url=SNA_BASE_URL + f"/sw-reporting/v1/tenants/{self.tenant_id}/security-events/templates",
                verify=False
            )
            if response.ok:
                security_events = dict(
                    [(item["id"], {"name": item["name"], "description": item["description"]}) for item in
                     response.json()['data']])
                log.info("SNAM Get SNA Events: Successful.")
                return security_events
            else:
                log.error("SNAM Get SNA Events: Unsuccessful.")
                response.raise_for_status()

        except HTTPError:
            if response.status_code == 401:
                log.error("SNAM Get SNA Events:: HTTP 401: Invalid credentials used.")
                exit()
            elif response.status_code == 404:
                log.error("SNAM Get SNA Events:: HTTP 404: Resource not found. Check URL validity.")
                exit()
        except ConnectionError:
            log.error(
                "SNAM Get SNA Events:: Connection: Check network connectivity to SNAM node or check URL validity.")
            exit()
        except Timeout:
            log.error("SNAM Get SNA Events:: Timeout: Re-attempt authentication method.")
            exit()
        except Exception as e:
            log.error(f"SNAM Get SNA Events:: Unknown exception: Deeper troubleshooting required to fix {e}")
            exit()

    def get_sna_internal_hosts(self):
        """
        Retrieve and return top breaching internal hosts list. Returns information about each host
        breaching threshold values.
        :param: None
        :return: (list[]) list containing SNA hosts represented as dict() objects
        """
        response = None
        try:
            response = self.session.get(
                url=SNA_BASE_URL + f"/sw-reporting/v1/tenants/{self.tenant_id}/internalHosts/alarms/topHosts",
                verify=False
            )
            if response.ok:
                log.info("SNAM Get Internal Hosts: Successful.")
                return response
            else:
                log.error("SNAM Get Internal Hosts: Unsuccessful.")
                response.raise_for_status()

        except HTTPError:
            if response.status_code == 401:
                log.error("SNAM Get Internal Hosts:: HTTP 401: Invalid credentials used.")
                exit()
            elif response.status_code == 404:
                log.error("SNAM Get Internal Hosts:: HTTP 404: Resource not found. Check URL validity.")
                exit()
        except ConnectionError:
            log.error(
                "SNAM Get Internal Hosts:: Connection: Check network connectivity to SNAM node or check URL validity.")
            exit()
        except Timeout:
            log.error("SNAM Get Internal Hosts:: Timeout: Re-attempt authentication method.")
            exit()
        except Exception as e:
            log.error(f"SNAM Get Internal Hosts:: Unknown exception: Deeper troubleshooting required to fix {e}")
            exit()

    def get_sna_external_hosts(self):
        """
        Retrieve and return top breaching internal hosts list. Returns information about each host
        breaching threshold values.
        :param: None
        :return: (list[]) list containing SNA hosts represented as dict() objects
        """
        response = None
        try:
            response = self.session.get(
                url=SNA_BASE_URL + f"/sw-reporting/v1/tenants/{self.tenant_id}/externalHosts/alarms/topHosts",
                verify=False
            )
            if response.ok:
                log.info("SNAM Get External Hosts: Successful.")
                return response
            else:
                log.error("SNAM Get External Hosts: Unsuccessful.")
                response.raise_for_status()

        except HTTPError:
            if response.status_code == 401:
                log.error("SNAM Get External Hosts:: HTTP 401: Invalid credentials used.")
                exit()
            elif response.status_code == 404:
                log.error("SNAM Get External Hosts:: HTTP 404: Resource not found. Check URL validity.")
                exit()
        except ConnectionError:
            log.error(
                "SNAM Get External Hosts:: Connection: Check network connectivity to SNAM node or check URL validity.")
            exit()
        except Timeout:
            log.error("SNAM Get External Hosts:: Timeout: Re-attempt authentication method.")
            exit()
        except Exception as e:
            log.error(f"SNAM Get External Hosts:: Unknown exception: Deeper troubleshooting required to fix {e}")
            exit()

    def get_sna_event_name_from_id(self, id):
        id_event_mapping = self.get_sna_events()
        return id_event_mapping[id]

    def get_sna_host_tagname_from_id_list(self, id_list):
        host_tagname_list = []
        id_tag_mapping = self.get_sna_host_tag_mapping()

        for id in id_list:
            if id in id_tag_mapping.keys():
                host_tagname_list.append(id_tag_mapping[id])
            else:
                host_tagname_list.append('Catch All')

        return host_tagname_list

    def consolidate_sw_top_hosts(self):
        """
        Retrieve and return top breaching internal and external hosts list. Returns information about each host
        breaching threshold values.
        :param: None
        :return: (list[]) list containing SNA hosts represented as dict() objects
        """
        internal_hosts_response = self.get_sna_internal_hosts()
        internal_hosts = []
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
                        "host_security_tags": deduplicate_list(
                            self.get_sna_host_tagname_from_id_list(json_response['data'][host_index]['hostGroupIds'])),
                        "source_security_events": [{
                            "name": self.get_sna_event_name_from_id(item['typeId'])['name'],
                            "description": self.get_sna_event_name_from_id(item['typeId'])['description'],
                            "severity": item['severity']
                        } for item in json_response['data'][host_index]['sourceSecurityEvents']],
                        "target_security_events": [{
                            "name": self.get_sna_event_name_from_id(item['typeId'])['name'],
                            "description": self.get_sna_event_name_from_id(item['typeId'])['description'],
                            "severity": item['severity']
                        } for item in json_response['data'][host_index]['targetSecurityEvents']],
                        "time_start": python_datetime_converter(json_response['header']['startTime']),
                        "time_end": python_datetime_converter(json_response['header']['endTime'])
                    }
                )
        else:
            internal_hosts = []

        external_hosts_response = self.get_sna_external_hosts()
        external_hosts = []

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
                        "host_security_tags": deduplicate_list(
                            self.get_sna_host_tagname_from_id_list(json_response['data'][host_index]['hostGroupIds'])),
                        "source_security_events": [{
                            "name": self.get_sna_event_name_from_id(item['typeId'])['name'],
                            "description": self.get_sna_event_name_from_id(item['typeId'])['description'],
                            "severity": item['severity']
                        } for item in json_response['data'][host_index]['sourceSecurityEvents']],
                        "target_security_events": [{
                            "name": self.get_sna_event_name_from_id(item['typeId'])['name'],
                            "description": self.get_sna_event_name_from_id(item['typeId'])['description'],
                            "severity": item['severity']
                        } for item in json_response['data'][host_index]['targetSecurityEvents']],
                        "time_start": python_datetime_converter(json_response['header']['startTime']),
                        "time_end": python_datetime_converter(json_response['header']['endTime'])
                    }
                )

        else:
            external_hosts = []

        return internal_hosts + external_hosts

    def generate_snam_kb(self):
        try:
            self.knowledge = {
                "STEALTHWATCH_ALARMS": self.consolidate_sw_top_hosts()
            }
            log.info("SNAM KB Update: Update Successful.")
        except Exception as e:
            log.error(f"SNAM KB Update: Update Unsuccessful. Exception hit: {e}")

    def store_snam_kb(self):
        try:
            self.generate_snam_kb()
            write_to_json(
                document=snam_kb_filepath,
                content=self.knowledge
            )
            log.info("SNAM KB Storage: Storage Successful")
        except Exception as e:
            log.error(f"SNAM KB Storage: Storage Unsuccessful. Exception hit: {e}")


if __name__ == '__main__':
    snam = SNAM()
    # snam.store_snam_kb()
    # pp(snam.get_sna_host_tag_mapping())
    snam.test_snam()
