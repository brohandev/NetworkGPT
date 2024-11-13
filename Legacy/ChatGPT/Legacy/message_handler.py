import json
import logging
import re

from Authentication.authentication import authenticate_controller
from Legacy.Authentication.credentials import OPENAI_COMPLETION_URL, DNA_CENTER_BASE_URL, VMANAGE_BASE_URL, ISE_BASE_URL, \
    ISEv_PORT, OPENAI_MODEL, OPENAI_TEMPERATURE
from Excel.excel_controller import api_knowledge_base_to_dict, openAI_prompt_knowledge_base_to_dict, DNAC_KB_INPUT, \
    VMANAGE_KB_INPUT, ISE_KB_INPUT, OPENAI_KB_INPUT
from prettyprinter import pprint as pp

log = logging.getLogger(__name__)

# intialize sessions with all network controllers, and pad headers with appropriate parameters
dnac_session, vmanage_session, ise_session = authenticate_controller()


def solve(chat):
    data = json.dumps({
        "model": OPENAI_MODEL,
        "messages": chat,
        "temperature": OPENAI_TEMPERATURE
    })
    response_json = openai_session.post(url=OPENAI_COMPLETION_URL, data=data)
    response = response_json.json()['choices'][0]['message']['content'].strip("\n")

    # ask ChatGPT which API call will be most relevant to answer user's question
    if response in ["LAN", "WAN", "Security"]:
        domain = response

        # artificially insert assistant and user prompts to add context to the overall conversation
        extended_chat = openAI_prompt_knowledge_base_to_dict(OPENAI_KB_INPUT, sheet_name="API_REQUEST")

        log.info(f"Domain Identified: {domain}")
        if domain == "LAN":
            # append assistant's input
            chat.append(extended_chat[0])
            # append user's input
            text = str(extended_chat[1]["content"])
            text += f"\nList of API Calls: {api_knowledge_base_to_dict(DNAC_KB_INPUT)}"
            extended_chat[1]["content"] = text
            chat.append(extended_chat[1])
        elif domain == "WAN":
            chat.append(extended_chat[2])
            text = str(extended_chat[3]["content"])
            text += f"\nList of API Calls: {api_knowledge_base_to_dict(VMANAGE_KB_INPUT)}"
            extended_chat[3]["content"] = text
            chat.append(extended_chat[3])
        elif domain == "Security":
            chat.append(extended_chat[4])
            text = str(extended_chat[5]["content"])
            text += f"\nList of API Calls: {api_knowledge_base_to_dict(ISE_KB_INPUT)}"
            extended_chat[5]["content"] = text
            chat.append(extended_chat[5])

        data = json.dumps({
            "model": OPENAI_MODEL,
            "messages": chat,
            "temperature": OPENAI_TEMPERATURE
        })
        response_json = openai_session.post(url=OPENAI_COMPLETION_URL, data=data)
        response = response_json.json()['choices'][0]['message']['content'].strip("\n")

        # extract API URL from the ChatGPT's response and make API call
        api_url = re.search(r"(\/[a-zA-Z0-9-]+)+", response).group()
        if domain == "LAN":
            url = DNA_CENTER_BASE_URL + api_url
            response = dnac_session.get(url=url, params={}, verify=False).json()['response']
        elif domain == "WAN":
            url = VMANAGE_BASE_URL + "/dataservice" + api_url
            response = vmanage_session.get(url=url, params={}, verify=False).json()
            response.pop("header")
        elif domain == "Security":
            url = ISE_BASE_URL + ISEv_PORT + api_url
            response = ise_session.get(url=url, params={}, verify=False).json()

        # request ChatGPT to make JSON content more human-readable
        formatted_chat = openAI_prompt_knowledge_base_to_dict(OPENAI_KB_INPUT, sheet_name="RESPONSE_FORMATTING")
        text = str(formatted_chat[0]["content"])
        text += f"\nContent: {response}"
        formatted_chat[0]["content"] = text
        chat.append(formatted_chat[0])
        data = json.dumps({
            "model": OPENAI_MODEL,
            "messages": chat,
            "temperature": OPENAI_TEMPERATURE
        })
        response_json = openai_session.post(url=OPENAI_COMPLETION_URL, data=data)
        response = response_json.json()['choices'][0]['message']['content'].strip("\n")

    return response


def ask_chatgpt(chat, role, message):
    chat.append({
        "role": role,
        "content": message
    })
    data = json.dumps({
        "model": OPENAI_MODEL,
        "messages": chat,
        "temperature": OPENAI_TEMPERATURE
    })
    response_json = openai_session.post(url=OPENAI_COMPLETION_URL, data=data)
    response = response_json.json()['choices'][0]['message']['content'].strip("\n")
    return response


def handle_message(message):
    chat = openAI_prompt_knowledge_base_to_dict(OPENAI_KB_INPUT, "INITIALIZATION")

    text = str(chat[1]["content"])
    text += f"\nQuestion: {message}"
    chat[1]["content"] = text

    response = solve(chat)

    return response


if __name__ == '__main__':
    message = "how many stars are in the galaxy"
    handle_message(message)
