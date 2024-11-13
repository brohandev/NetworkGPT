import json
import logging
from pprint import pprint as pp

from Authentication.authentication import openAI_authenticate
from Legacy.Authentication.credentials import OPENAI_COMPLETION_URL, OPENAI_MODEL, OPENAI_TEMPERATURE
from Excel.excel_controller import openAI_prompt_knowledge_base_to_dict, OPENAI_KB_INPUT

log = logging.getLogger(__name__)


class ChatGPTBot:
    def __init__(self):
        self.session = openAI_authenticate()
        self.system = json.dumps(openAI_prompt_knowledge_base_to_dict(doc=OPENAI_KB_INPUT, sheet_name="SYSTEM_INIT")[0])
        self.chat_history = [{"role": "system", "content": self.system}]
        result = self.execute()
        if result:
            log.info("ChatGPT Object Instantiation: Instantiation Successful")
        else:
            log.error("ChatGPT Object Instantiation Unsuccessful")
            exit()

    def execute(self):
        data = json.dumps({
            "model": OPENAI_MODEL, "messages": self.chat_history, "temperature": OPENAI_TEMPERATURE})
        response_json = self.session.post(url=OPENAI_COMPLETION_URL, data=data)
        pp(response_json.json())
        result = response_json.json()['choices'][0]['message']['content'].strip("\n")
        return result

    def ask_chatgpt(self, user_prompt):
        # Flush chat_history and reinitialize with system prompt
        self.chat_history = [{"role": "system", "content": self.system}]
        self.chat_history.append({"role": "user", "content": user_prompt})
        result = self.execute()
        self.chat_history.append({"role": "assistant", "content": result})
        return result
