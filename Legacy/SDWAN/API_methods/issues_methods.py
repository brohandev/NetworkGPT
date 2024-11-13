from Legacy.Authentication.credentials import VMANAGE_BASE_URL, VMANAGE_API_URL
from SDWAN.API_methods.url import VMANAGE_ALARMS_URI
from pprint import pprint as pp

# TODO
# session = vmanage_authenticate()
session = None


def get_vmanage_alarms():
    """
        Retrieve and return wan alarms list. Returns information about each alarm and the devices it affects.
        :param: None
        :return: (list[]) list containing SDWAN alarms/problems represented as dict() objects
        """
    url = VMANAGE_BASE_URL + VMANAGE_API_URL + VMANAGE_ALARMS_URI
    response = session.get(url=url, verify=False)
    sdwan_alarms_list = []

    if response.ok:
        sdwan_alarms_list = response.json()['data']
    else:
        print(response.status_code)
        print("Failed to get list of devices " + str(response.text))

    return sdwan_alarms_list


if __name__ == '__main__':
    pp(get_vmanage_alarms())
