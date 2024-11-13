from Authentication.authentication import ise_authenticate
from Legacy.Authentication.credentials import ISE_BASE_URL
from ISE.API_methods.url import ISE_POLICY_SET_URI, ISE_AUTHENTICATION_POLICIES_URI, ISE_AUTHORIZATION_PROFILE_URI, \
    ISE_AUTHORIZATION_PROFILE_DETAILS_URI, ISE_AUTHORIZATION_POLICIES_URI, ISE_LOCAL_EXCEPTION_URI
from pprint import pprint as pp

# TODO
# session = ise_authenticate()
session = None


def get_ise_default_policy_set():
    """
    Retrieve and return ise policy set.
    :param: None
    :return: (str) policy set ID
    """
    url = ISE_BASE_URL + ISE_POLICY_SET_URI
    response = session.get(url=url, verify=False)
    policy_set_id = None
    if response.ok:
        policy_set_id = response.json()['response'][0]['id']
    else:
        print(response.status_code)
        print("Failed to get ISE policy set ID " + str(response.text))

    return policy_set_id


def get_ise_authentication_policies():
    """
    Retrieve and return authentication policies list. Returns information about each authentication policy.
    :param: None
    :return: (list[]) list containing authentication policies represented as dict() objects
    """
    policy_set_id = get_ise_default_policy_set()
    url = ISE_BASE_URL + ISE_AUTHENTICATION_POLICIES_URI.format(policy_set=policy_set_id)
    response = session.get(url=url, verify=False)
    authentication_list = []

    if response.ok:
        authentication_list = response.json()['response']
    else:
        print(response.status_code)
        print("Failed to get list of authentication policies " + str(response.text))

    return authentication_list


def get_ise_authorization_policies():
    """
    Retrieve and return authorization policies list. Returns information about each authorization policy.
    :param: None
    :return: (list[]) list containing authorization policies represented as dict() objects
    """
    policy_set_id = get_ise_default_policy_set()
    url = ISE_BASE_URL + ISE_AUTHORIZATION_POLICIES_URI.format(policy_set=policy_set_id)
    response = session.get(url=url, verify=False)
    authorization_list = []

    if response.ok:
        authorization_list = response.json()['response']
    else:
        print("Failed to get list of authorization policies " + str(response.text))

    return authorization_list


def get_ise_authorization_profiles():
    """
    Retrieve and return authorization profiles list. Returns information about each authorization profile.
    :param: None
    :return: (list[]) list containing authorization profiles represented as dict() objects
    """
    # Retrieve authorization profiles -> list of name:id
    url = ISE_BASE_URL + ISE_AUTHORIZATION_PROFILE_URI
    response = session.get(url=url, verify=False)
    cleaned_profile_list = []
    if response.ok:
        url = ISE_BASE_URL + ISE_AUTHORIZATION_PROFILE_DETAILS_URI
        profile_list = response.json()['SearchResult']['resources']
        for profile_dict in profile_list:
            del profile_dict['description']
            del profile_dict['link']

            response = session.get(url=url.format(authorization_profile_ID=profile_dict['id']), verify=False)

            if response.ok:
                profile_details_dict = response.json()['AuthorizationProfile']
                profile_dict['accessType'] = profile_details_dict['accessType']
                if 'vlan' in profile_details_dict.keys():
                    profile_dict['vlan'] = profile_details_dict['vlan']['nameID']
                else:
                    profile_dict['vlan'] = 'No VLAN'
                del profile_dict['id']
                cleaned_profile_list.append(profile_dict)
            else:
                print("Failed to get detailed list of authorization policies " + str(response.text))

    else:
        pp("Failed to get list of authorization profiles " + str(response.text))

    return cleaned_profile_list


def get_ise_local_exceptions():
    """
    Retrieve and return local exceptions list. Returns information about each local exception.
    :param: None
    :return: (list[]) list containing local exceptions represented as dict() objects
    """
    policy_set_id = get_ise_default_policy_set()
    url = ISE_BASE_URL + ISE_LOCAL_EXCEPTION_URI.format(policy_set=policy_set_id)
    response = session.get(url=url, verify=False)

    exception_list = []
    if response.ok:
        exception_list = response.json()['response']
    else:
        print(response.status_code)
        print("Failed to get list of local exceptions " + str(response.text))

    return exception_list


if __name__ == '__main__':
    pp(get_ise_local_exceptions())