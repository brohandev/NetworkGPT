import json
import logging
from threading import Thread
from time import sleep

from Authentication.credentials import WEBEX_BOT_ACCESS_TOKEN, WEBEX_BOT_NAME, WEBEX_APPROVED_ROOM, WEBEX_RODEV_ROOM, WEBEX_TONXU_ROOM
from Auxiliary.shared_functions import write_to_json
from Excel.excel_controller import DNAC_KB_PATH, VMANAGE_KB_PATH, DEVICE_DOMAIN_MAPPING_PATH
from SDA.consolidator import generate_DNAC_KB
from SDWAN.consolidator import generate_VMANAGE_KB
from ISE.consolidator import generate_ISE_KB
from Stealthwatch.consolidator import generate_SW_KB
from webex_bot.webex_bot import WebexBot
from Webex.answer_question import AnswerCommand


log = logging.getLogger(__name__)


def generate_device_domain_mapping():
    try:
        with open(DNAC_KB_PATH, "r") as file:
            dnac_json_data = json.load(file)
        with open(VMANAGE_KB_PATH, "r") as file:
            vmanage_json_data = json.load(file)

        device_domain_mapping = {}
        lan_devices = dnac_json_data["LAN_DEVICES"]
        lan_clients = dnac_json_data["CLIENTS"]
        for device in lan_devices:
            device_domain_mapping[device["hostname"]] = "LAN"
        for client in lan_clients:
            device_domain_mapping[client["hostname"]] = "CLIENT"
        wan_devices = vmanage_json_data["WAN_DEVICES"]
        for device in wan_devices:
            device_domain_mapping[device["host-name"]] = "WAN"

        write_to_json(document=DEVICE_DOMAIN_MAPPING_PATH, content=device_domain_mapping)
        log.info("Device Domain Mapping: Update Successful")
    except:
        log.info("Device Domain Mapping: Update Unsuccessful")


def knowledge_base_initialization():
    # while True:
    try:
        log.info("Overall KB Update: Update Commencing...")
        generate_DNAC_KB()
        generate_VMANAGE_KB()
        generate_ISE_KB()
        generate_SW_KB()
        generate_device_domain_mapping()
        log.info("Overall KB Update: Completed; Update Successful")
    except:
        log.info("Overall KB Update: Completed; Update Unsuccessful")

        # Updates knowledge base every 5 minutes
        # sleep(3600)


def webex_bot_initialization():
    # Create a Webex Bot Object
    bot = WebexBot(teams_bot_token=WEBEX_BOT_ACCESS_TOKEN,
                   bot_name=WEBEX_BOT_NAME,
                   approved_rooms=[WEBEX_APPROVED_ROOM, WEBEX_RODEV_ROOM],
                   include_demo_commands=False)

    # Clear default commands
    bot.commands.clear()

    # Add custom command, and set it as the new default command
    bot.add_command(AnswerCommand())
    bot.help_command = AnswerCommand()

    # Call `run` for the bot to wait for incoming messages.
    bot.run()


if __name__ == '__main__':
    # Thread(target=knowledge_base_initialization).start()
    # Thread(target=webex_bot_initialization).start()
    # knowledge_base_initialization()
    # generate_device_domain_mapping()
    webex_bot_initialization()
    # print(DNAC_KB_PATH)
