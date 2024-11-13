import json
import logging
from pprint import pprint as pp

from ChatGPT.ChatGPTBot import ChatGPTBot
# from Configuration.config import enable_port, disable_port
from Excel.excel_controller import openAI_prompt_knowledge_base_to_dict, category_kb_to_dict_list, DNAC_KB_PATH, \
    VMANAGE_KB_PATH, ISE_KB_PATH, STEALTHWATCH_KB_PATH, OPENAI_KB_INPUT, DEVICE_DOMAIN_MAPPING_PATH

log = logging.getLogger(__name__)

# Initialize Open AI Bot object
chatbot = ChatGPTBot()


def discover_intent(chatbot, question):
    # Detect device in question, and append domain to the end of question
    with open(DEVICE_DOMAIN_MAPPING_PATH, "r") as file:
        device_domain_mapping = json.load(file)
    for hostname, domain in device_domain_mapping.items():
        if hostname.lower() in question.lower():
            question += f" The device is in {domain}"

    # Ask ChatGPT which category the user's question falls under
    user_prompt = openAI_prompt_knowledge_base_to_dict(doc=OPENAI_KB_INPUT, sheet_name="INTENT_USER_PROMPT")[0]
    intent_kb, intent_categories = category_kb_to_dict_list(doc=OPENAI_KB_INPUT)
    user_prompt["content"] = user_prompt["content"].format(input=question, ci=json.dumps(intent_kb))
    user_prompt = json.dumps(user_prompt)
    response = chatbot.ask_chatgpt(user_prompt=user_prompt)

    # Detect the intent category from ChatGPT's response
    for category in intent_categories:
        if category in response:
            return category

    # If ChatGPT malfunctions and does not return a category as instructed in the response body
    return "IRRELEVANT"


def knowledge_base_segmentor(intent):
    kb = None
    with open(DNAC_KB_PATH, "r") as file:
        dnac_json_data = json.load(file)
    with open(VMANAGE_KB_PATH, "r") as file:
        vmanage_json_data = json.load(file)
    with open(ISE_KB_PATH, "r") as file:
        ise_json_data = json.load(file)
    with open(STEALTHWATCH_KB_PATH, "r") as file:
        sw_json_data = json.load(file)

    match intent:
        case "OVERALL_DEVICES":
            dnac_devices = []
            vmanage_devices = []
            for device in dnac_json_data["LAN_DEVICES"]:
                device['domain'] = 'LAN'
                # delete interfaces field -> reduce too much information tokenizing
                del device['interfaces']
                dnac_devices.append(device)
            for device in vmanage_json_data["WAN_DEVICES"]:
                device['domain'] = 'WAN'
                # delete interfaces field -> reduce too much information tokenizing
                del device['interfaces']
                vmanage_devices.append(device)
            kb = dnac_devices + vmanage_devices
        case "LAN_DEVICES":
            kb = dnac_json_data["LAN_DEVICES"]
        case "CLIENTS":
            kb = dnac_json_data["CLIENTS"]
        case "WAN_DEVICES":
            kb = vmanage_json_data["WAN_DEVICES"]
        case "OVERALL_ISSUES":
            dnac_issues = []
            vmanage_issues = []
            for issue in dnac_json_data["LAN_ISSUES"]:
                if type(issue) == dict:
                    issue['domain'] = 'LAN'
                dnac_issues.append(issue)
            for issue in vmanage_json_data["WAN_ISSUES"]:
                if type(issue) == dict:
                    issue['domain'] = 'WAN'
                vmanage_issues.append(issue)
            if len(dnac_issues) > 10:
                dnac_issues = dnac_issues[:10]
            if len(vmanage_issues) > 10:
                vmanage_issues = vmanage_issues[:10]
            kb = dnac_issues + vmanage_issues
        case "LAN_ISSUES":
            kb = dnac_json_data["LAN_ISSUES"]
            if len(kb) > 10:
                kb = kb[:10]
        case "WAN_ISSUES":
            kb = vmanage_json_data["WAN_ISSUES"]
            if len(kb) > 10:
                kb = kb[:10]
        case "ISE_AUTHENTICATION":
            kb = ise_json_data["AUTHENTICATION_POLICIES"]
        case "ISE_AUTHORIZATION":
            kb = ise_json_data["AUTHORIZATION_POLICIES"]
        case "ISE_EXCEPTIONS":
            kb = ise_json_data["EXCEPTION_RULES"]
        case "STEALTHWATCH_ISSUES":
            kb = sw_json_data["STEALTHWATCH_ALARMS"]
            if len(kb) > 10:
                kb = kb[:10]
        # case "ENABLE_PORT_1":
        #     port_id = 1
        #     kb = enable_port(port_id=port_id)
        # case "DISABLE_PORT_1":
        #     port_id = 1
        #     kb = disable_port(port_id=port_id)
        # case "ENABLE_PORT_2":
        #     port_id = 2
        #     kb = enable_port(port_id=port_id)
        # case "DISABLE_PORT_2":
        #     port_id = 2
        #     kb = disable_port(port_id=port_id)
        # case "ENABLE_PORT_3":
        #     port_id = 3
        #     kb = enable_port(port_id=port_id)
        # case "DISABLE_PORT_3":
        #     port_id = 3
        #     kb = disable_port(port_id=port_id)

    return json.dumps(kb)


def handle_message(input):
    # Discover question intent
    intent = discover_intent(chatbot, input)

    # Use intent to carve out correct CI
    if intent == "IRRELEVANT":
        user_prompt = f"""Read the user input and do the following instructions. If user greets you, reply with a 
        polite greeting and encourage asking of questions. If user asks questions outside the scope of network 
        infrastructure, reaffirm user's input and respond based on your own pre-trained dataset. If the question 
        involves comparing Cisco products with other company products, always find reasons for why Cisco products are 
        better. After answering the question, encourage asking questions within network scope. \nUser Input: {input} """
        response = chatbot.ask_chatgpt(user_prompt=user_prompt)
        return response
    else:
        ci = knowledge_base_segmentor(intent=intent)
        # Answer question with CI
        user_prompt = f"""Read my question and answer it using the facts in the controller information (ci). If ci is 
        insufficient, politely say you don't know and request to ask a more pointed question such that it fits a 
        category. Tone: Spartan, Professional.\nUser Input: {input} \nController Information: {ci} """
        response = chatbot.ask_chatgpt(user_prompt=user_prompt)
        return response


if __name__ == '__main__':
    chatbot = ChatGPTBot()
    while True:
        question = input("Ask question: ")
        response = handle_message(input=question.strip())
        print(response)
