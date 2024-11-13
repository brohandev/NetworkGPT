from paramiko import (
    AutoAddPolicy,
    SSHClient
)
from pprint import pprint as pp
from time import sleep

from Legacy.Authentication.credentials import CCTV_SWITCH_IP, CCTV_SWITCH_USER, CCTV_SWITCH_PASSWORD


def retrieve_switchport_information(port_id: int):
    # try:
    ssh_client = SSHClient()
    ssh_client.set_missing_host_key_policy(AutoAddPolicy())
    ssh_client.connect(hostname="10.68.57.148",
                       username="admin",
                       password="admin"
                       )

    # stdin, stdout, stderr = ssh_client.exec_command("show ip interface brief \n")
    # output = stdout.readlines()
    # pp(output)

    # except:
    #     return None


# def disable_port(port_id: int):
#     # retrieve incumbent device switch port configuration
#     port_info = retrieve_switchport_information(port_id=port_id)
#     if bool(port_info):
#         # push configuration to disable specified port
#         if port_info['enabled']:
#             try:
#                 dashboard.switch.updateDeviceSwitchPort(
#                     serial=MERAKI_SWITCH_SERIAL,
#                     portId=port_id,
#                     enabled=False
#                 )
#                 return f"Your request is being processed, and port {port_id} will be successfully disabled."
#             except:
#                 return "The port cannot be disabled right now. Contact your administrator."
#         else:
#             return "The port specified is already disabled. Pick another port or enable this port instead."
#     else:
#         return "Please check if the stated port number is correct"
#
#
# def enable_port(port_id: int):
#     # retrieve incumbent device switch port configuration
#     port_info = retrieve_switchport_information(port_id=port_id)
#     if bool(port_info):
#         # push configuration to disable specified port
#         if not port_info['enabled']:
#             try:
#                 dashboard.switch.updateDeviceSwitchPort(
#                     serial=MERAKI_SWITCH_SERIAL,
#                     portId=port_id,
#                     enabled=True
#                 )
#                 return f"Your request is being processed, and port {port_id} will be successfully enabled."
#             except:
#                 return "The port cannot be enabled right now. Contact your administrator."
#         else:
#             return "The port specified is already enabled. Pick another port or disable this port instead."
#     else:
#         return "Please check if the stated port number is correct"


if __name__ == '__main__':
    retrieve_switchport_information(1)
