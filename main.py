# package import
import logging
from threading import Thread
from time import sleep

# local import
from Controllers.dnac import DNAC
from Controllers.ise import ISE
from Controllers.vmanage import vMANAGE
from Controllers.snam import SNAM
from Controllers.knox import Knox
from Controllers.webex import Chatbot

logging.basicConfig()
log = logging.getLogger("Main_Program_Execution")
log.setLevel(logging.INFO)


def refresh_knowledge_base():
    # Wait for 5 minute(s) before refreshing again
    refresh_rate = 900

    # Instantiate SDN controller objects
    dnac = DNAC()
    ise = ISE()
    vmanage = vMANAGE()
    knox = Knox()
    # snam = SNAM()

    while True:
        try:
            log.info("Refreshing knowledge base...")
            dnac.store_lan_kb()
            ise.store_ise_kb()
            vmanage.store_wan_kb()
            knox.store_knox_kb()
            # snam.store_snam_kb()
            log.info("Knowledge Base Update: Successful.")

            sleep(secs=refresh_rate)

        except Exception as e:
            log.error(f"Knowledge Base Update: Unsuccessful. Error: {e}")


def run_chatbot():
    try:
        log.info("Instantiating and running NetworkGPT chatbot...")
        chatbot = Chatbot()
        chatbot.run()

    except Exception as e:
        log.error(f"Run Chatbot: Unsuccessful. Error: {e}")


def main():
    # Asynchronous knowledge base refresh
    # Thread(target=refresh_knowledge_base).start()

    # persistent operation of MAMPUlator Webex chatbot
    run_chatbot()


main()
