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
    write_to_json
)
from Authentication.credentials import (
    ISE_BASE_URL,
    ISE_APISERVICE_METHOD,
    ISE_ENCODED_AUTH
)
from Storage.filepaths import (
    ise_kb_filepath
)

logging.basicConfig()
log = logging.getLogger("ISE_KB_Generation")
log.setLevel(logging.INFO)

warnings.filterwarnings("ignore", category=InsecureRequestWarning)


class ISE:
    def __init__(self):
        self.session = self.authenticate()
        self.policy_set_id = self.get_ise_default_policy_set()
        self.knowledge = self.initialize_base_knowledge()

    @staticmethod
    def authenticate():
        """
        Creates a Session object and authenticates with the primary ISE PAN node. Upon successful HTTP Status Code,
        updates Session object with the credentials and returns object to caller. Upon failure, attempts to enable API
        Gateway Service on all ISE nodes and re-attempts authentication. Upon failure during any of the previous steps,
        the program stops and exits.
        """
        response = None
        update_response = None
        session = Session()

        try:
            response = get(url=ISE_BASE_URL + ISE_APISERVICE_METHOD + "/get",
                           auth=ISE_ENCODED_AUTH,
                           headers={
                               'Content-Type': 'application/json',
                               'Accept': 'application/json'
                           },
                           verify=False)
            if response.ok:
                session.auth = ISE_ENCODED_AUTH
                session.verify = False
                headers = {
                    'Content-Type': "application/json",
                    'Accept': 'application/json'
                }
                session.headers.update(headers)

                disabled_ise_nodes = []
                for response_dict in response.json():
                    if not response_dict["isEnabled"]:
                        disabled_ise_nodes.append(response_dict["hostname"])
                        log.warning(f'ISE Node {response_dict["hostname"]} has disabled API Gateway Service. Will '
                                    f'enable now.')
                        log.info('Run ISE authentication method again.')

                update_response = post(url=ISE_BASE_URL + ISE_APISERVICE_METHOD + "/update",
                                       auth=ISE_ENCODED_AUTH,
                                       headers={
                                           "Accept": "application/json",
                                       },
                                       json=[
                                           {
                                               "hostname": f"{hostname}",
                                               "isEnabled": True
                                           } for hostname in disabled_ise_nodes
                                       ],
                                       verify=False)
                if not update_response.ok:
                    update_response.raise_for_status()
                else:
                    log.info(f'ISE Authentication: Successful. Session headers updated.')
            else:
                response.raise_for_status()

        except HTTPError:
            if response.status_code == 401 or update_response.status_code == 401:
                log.error('ISE Authentication: HTTP Total Failure: Invalid URL used.')
            if response.status_code == 403 or update_response.status_code == 403:
                log.error('ISE Authentication: HTTP 403: Invalid credentials used.')
            exit()
        except ConnectionError:
            log.error("ISE Authentication: Connection: Check network connectivity to ISE node or check URL validity.")
            exit()
        except Timeout:
            log.error("ISE Authentication: Timeout: Re-attempt authentication method.")
            exit()
        except Exception as e:
            log.error(f"ISE Authentication: Unknown exception: Deeper troubleshooting required to fix {e}")
            exit()

        return session

    def initialize_base_knowledge(self):
        with open(ise_kb_filepath, "r") as file:
            ise_base_kb = json.load(file)
        return ise_base_kb

    def get_ise_default_policy_set(self):
        """
        Retrieve and return ise policy set.
        :param: None
        :return: (str) policy set ID
        """

        policy_set_id = None
        response = None
        try:
            response = self.session.get(url=ISE_BASE_URL + "/api/v1/policy/network-access/policy-set",
                                        verify=False)
            if response.ok:
                policy_set_id = response.json()['response'][0]['id']
                log.info("ISE Get Default Policy Set: Successful.")
            else:
                log.error("ISE Get Default Policy Set: Failed.")
                response.raise_for_status()

        except HTTPError:
            if response.status_code == 401:
                log.error("ISE Get Default Policy Set:: HTTP 401: Invalid credentials used.")
                exit()
            elif response.status_code == 404:
                log.error("ISE Get Default Policy Set:: HTTP 404: Resource not found. Check URL validity.")
                exit()
        except ConnectionError:
            log.error("ISE Get Default Policy Set:: Connection: Check network connectivity to DNAC node or check URL "
                      "validity.")
            exit()
        except Timeout:
            log.error("ISE Get Default Policy Set:: Timeout: Re-attempt authentication method.")
            exit()
        except Exception as e:
            log.error(f"ISE Get Default Policy Set:: Unknown exception: Deeper troubleshooting required to fix {e}")
            exit()

        return policy_set_id

    def get_ise_authentication_policies(self):
        """
        Retrieve and return authentication policies list. Returns information about each authentication policy.
        :param: None
        :return: (list[]) list containing authentication policies represented as dict() objects
        """
        authentication_list = []
        response = None
        try:
            policy_set_id = self.policy_set_id
            response = self.session.get(
                url=ISE_BASE_URL + f"/api/v1/policy/network-access/policy-set/{policy_set_id}/authentication",
                verify=False
            )
            if response.ok:
                authentication_list = response.json()['response']
            else:
                log.error("ISE Get Authentication Policies: Failed.")
                response.raise_for_status()

        except HTTPError:
            if response.status_code == 401:
                log.error("ISE Get Authentication Policies:: HTTP 401: Invalid credentials used.")
                exit()
            elif response.status_code == 404:
                log.error("ISE Get Authentication Policies:: HTTP 404: Resource not found. Check URL validity.")
                exit()
        except ConnectionError:
            log.error("ISE Get Authentication Policies:: Connection: Check network connectivity to DNAC node or check "
                      "URL validity.")
            exit()
        except Timeout:
            log.error("ISE Get Authentication Policies:: Timeout: Re-attempt authentication method.")
            exit()
        except Exception as e:
            log.error(f"ISE Get Authentication Policies:: Unknown exception: Deeper troubleshooting required to fix {e}")
            exit()

        return authentication_list

    def get_ise_authorization_policies(self):
        """
        Retrieve and return authorization policies list. Returns information about each authorization policy.
        :param: None
        :return: (list[]) list containing authorization policies represented as dict() objects
        """
        authorization_list = []
        response = None
        try:
            policy_set_id = self.policy_set_id
            response = self.session.get(
                url=ISE_BASE_URL + f"/api/v1/policy/network-access/policy-set/{policy_set_id}/authorization",
                verify=False)
            if response.ok:
                authorization_list = response.json()['response']
            else:
                log.error("ISE Get Authorization Policies: Failed.")
                response.raise_for_status()

        except HTTPError:
            if response.status_code == 401:
                log.error("ISE Get Authorization Policies:: HTTP 401: Invalid credentials used.")
                exit()
            elif response.status_code == 404:
                log.error("ISE Get Authorization Policies:: HTTP 404: Resource not found. Check URL validity.")
                exit()
        except ConnectionError:
            log.error("ISE Get Authorization Policies:: Connection: Check network connectivity to DNAC node or check "
                      "URL validity.")
            exit()
        except Timeout:
            log.error("ISE Get Authorization Policies:: Timeout: Re-attempt authentication method.")
            exit()
        except Exception as e:
            log.error(f"ISE Get Authorization Policies:: Unknown exception: Deeper troubleshooting required to fix {e}")
            exit()

        return authorization_list

    def get_ise_authorization_profiles(self):
        """
        Retrieve and return authorization profiles list. Returns information about each authorization profile.
        :param: None
        :return: (list[]) list containing authorization profiles represented as dict() objects
        """
        # Retrieve authorization profiles -> list of name:id
        response = None
        try:
            response = self.session.get(url=ISE_BASE_URL + "/ers/config/authorizationprofile",
                                        verify=False)
            cleaned_profile_list = []
            if response.ok:
                profile_list = response.json()['SearchResult']['resources']
                for profile_dict in profile_list:
                    del profile_dict['description']
                    del profile_dict['link']

                    response = self.session.get(url=ISE_BASE_URL + f"/ers/config/authorizationprofile/{profile_dict['id']}",
                                           verify=False)
                    if response.ok:
                        profile_details_dict = response.json()['AuthorizationProfile']
                        profile_dict['accessType'] = profile_details_dict['accessType']
                        if 'vlan' in profile_details_dict.keys():
                            profile_dict['vlan'] = profile_details_dict['vlan']['nameID']
                        else:
                            profile_dict['vlan'] = 'No VLAN'
                        del profile_dict['id']
                        cleaned_profile_list.append(profile_dict)
                        return cleaned_profile_list
                    else:
                        log.error("ISE Get Authorization Profiles: Failed to get detailed list.")
                        response.raise_for_status()
            else:
                log.error("ISE Get Authorization Profiles: Failed to get initial list.")
                response.raise_for_status()

        except HTTPError:
            if response.status_code == 401:
                log.error("ISE Get Authorization Profiles:: HTTP 401: Invalid credentials used.")
                exit()
            elif response.status_code == 404:
                log.error("ISE Get Authorization Profiles:: HTTP 404: Resource not found. Check URL validity.")
                exit()
        except ConnectionError:
            log.error("ISE Get Authorization Profiles:: Connection: Check network connectivity to DNAC node or check "
                      "URL validity.")
            exit()
        except Timeout:
            log.error("ISE Get Authorization Profiles:: Timeout: Re-attempt authentication method.")
            exit()
        except Exception as e:
            log.error(f"ISE Get Authorization Profiles:: Unknown exception: Deeper troubleshooting required to fix {e}")
            exit()

    def consolidate_authentication_policy_information(self):
        """
        1. Retrieve authentication policy list and policy-associated fields
        2. Trim irrelevant fields
        :return: (list[]) list containing authentication policy information represented as nested dict() objects
        """
        auth_policy_list = self.get_ise_authentication_policies()
        policy_list = []
        for policy in auth_policy_list:
            stripped_policy_dict = {k: policy[k] for k in policy.keys() & {
                'rule',
                'identitySourceName'
            }}

            policy_rule = stripped_policy_dict['rule']
            stripped_rule_dict = {k: policy_rule[k] for k in policy_rule.keys() & {
                'name',
                'hitCounts',
                'state',
                'condition'
            }}

            # Move onto next authentication policy if current policy is disabled -> only account for enabled ones
            if stripped_rule_dict['state'] == 'disabled':
                continue

            conditions = []
            rule_condition = stripped_rule_dict['condition']
            condition_type = "ConditionReference"
            if rule_condition is not None:
                stripped_condition_dict = {k: rule_condition[k] for k in rule_condition.keys() & {
                    'conditionType',
                    'name',
                    'description',
                    'children'
                }}

                if 'children' in stripped_condition_dict.keys():
                    condition_type = stripped_condition_dict['conditionType']
                    for child_condition in stripped_condition_dict['children']:
                        conditions.append({
                            'name': child_condition['name'],
                            'description': child_condition['description']
                        })
                else:
                    conditions.append({
                        'name': stripped_condition_dict['name'],
                        'description': stripped_condition_dict['description']
                    })
            else:
                conditions.append({
                    'name': 'Default',
                    'description': 'Default'
                })

            revised_policy = {
                'name': stripped_rule_dict['name'],
                'state': stripped_rule_dict['state'],
                'hits': stripped_rule_dict['hitCounts'],
                'identitySources': stripped_policy_dict['identitySourceName'],
                'conditionType': condition_type,
                'conditions': conditions
            }

            policy_list.append(revised_policy)

        return policy_list

    def consolidate_authorization_policy_information(self):
        # Retrieve list of authorization policies and trim irrelevant fields
        auth_policy_list = self.get_ise_authorization_policies()
        auth_profile_list = self.get_ise_authorization_profiles()
        policy_list = []

        for policy in auth_policy_list:
            stripped_policy_dict = {k: policy[k] for k in policy.keys() & {
                'rule',
                'profile',
                'securityGroup'
            }}

            policy_rule = stripped_policy_dict['rule']
            stripped_rule_dict = {k: policy_rule[k] for k in policy_rule.keys() & {
                'name',
                'hitCounts',
                'state',
                'condition'
            }}

            # Move onto next authorization policy if current policy is disabled -> only account for enabled ones
            if stripped_rule_dict['state'] == 'disabled':
                continue

            conditions = []
            rule_condition = stripped_rule_dict['condition']
            condition_type = "ConditionReference"
            if rule_condition is not None:
                stripped_condition_dict = {k: rule_condition[k] for k in rule_condition.keys() & {
                    'name',
                    'conditionType',
                    'children',
                    'dictionaryName',
                    'attributeName',
                    'operator',
                    'attributeValue',
                    'description'
                }}

                if 'children' in stripped_condition_dict.keys():
                    condition_type = stripped_condition_dict['conditionType']
                    for child_condition in stripped_condition_dict['children']:
                        if child_condition['conditionType'] == 'ConditionReference':
                            conditions.append({
                                'name': child_condition['name'],
                                'description': child_condition['description']
                            })
                        elif child_condition['conditionType'] == 'ConditionAttributes':
                            conditions.append({
                                'name': child_condition['dictionaryName'],
                                'description': child_condition['attributeName'] + " " + child_condition[
                                    'operator'] + " " + child_condition['attributeValue']
                            })
                else:
                    condition_type = stripped_condition_dict['conditionType']
                    if condition_type == 'ConditionReference':
                        conditions.append({
                            'name': stripped_condition_dict['name'],
                            'description': stripped_condition_dict['description']
                        })
                    elif condition_type == 'ConditionAttributes':
                        conditions.append({
                            'name': stripped_condition_dict['dictionaryName'],
                            'description': stripped_condition_dict['attributeName'] + " " + stripped_condition_dict[
                                'operator'] + " " + stripped_condition_dict['attributeValue']
                        })

            else:
                conditions.append({
                    'name': 'Default',
                    'description': 'Default'
                })

            # Retrieve list of authorization profiles
            profile_list = stripped_policy_dict['profile']
            revised_profile_list = []
            for profile in profile_list:
                for auth_profile in auth_profile_list:
                    if profile == auth_profile['name']:
                        revised_profile_list.append(
                            {
                                'profileName': profile,
                                'vlan': auth_profile['vlan']
                            }
                        )
                        break

            revised_policy = {
                'name': stripped_rule_dict['name'],
                'state': stripped_rule_dict['state'],
                'hits': stripped_rule_dict['hitCounts'],
                'conditionType': condition_type,
                'conditions': conditions,
                'profile': revised_profile_list,
                'securityGroupTag (SGT)': stripped_policy_dict['securityGroup']
            }

            policy_list.append(revised_policy)

        return policy_list

    def generate_ise_kb(self):
        try:
            self.knowledge = {
                "AUTHENTICATION_POLICIES": self.consolidate_authentication_policy_information(),
                "AUTHORIZATION_POLICIES": self.consolidate_authorization_policy_information()
            }
            log.info("ISE KB Update: Update Successful")
        except Exception as e:
            log.error(f"ISE KB Update: Update Unsuccessful. Exception hit: {e}")

    def store_ise_kb(self):
        try:
            self.generate_ise_kb()
            write_to_json(
                document=ise_kb_filepath,
                content=self.knowledge
            )
            log.info("ISE KB Storage: Storage Successful")
        except Exception as e:
            log.error(f"ISE KB Storage: Storage Unsuccessful. Exception hit: {e}")


if __name__ == '__main__':
    ise = ISE()
    ise.store_ise_kb()
