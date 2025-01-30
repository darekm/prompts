import asyncio
import json
import pathlib

from src.helpers.chat_connector import ChatConnector

PROMPT_DIR = pathlib.Path(__file__).parent.parent

class ChatPrompt:
    def __init__(self,logger):
        self.model = 'openai'
        self.logger = logger
        self.billed_tokens = 0
        self.path = PROMPT_DIR / 'prompt'

    async def completion(self, prompt, model):
        chat = ChatConnector(self.logger)
        chat.init_model(model)
        await asyncio.sleep(0.1)
        response = await chat.ask(prompt)
        self.billed_tokens += chat.billed_tokens
        return response
    

    async def extract_fk(self, text, model):
        # self.logger.debug(f'Completion  {model}  invoice')
        result = await self.completion(self.prompt('fg',text), self.model)
        return result
    
    def prompt(self,name, text):
        with open(self.path / 'system_chat.md', 'r') as file:
            body_system = file.read()
        return f'{body_system} \n####\n{text}'
        # return MY_INVOICE_EXTRUDER_TMPL.replace('{context_str}', document) 
