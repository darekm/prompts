import asyncio
import json
from datetime import datetime

from src.helpers.chat_connector import ChatConnector


class ChatPrompt:
    def __init__(self):
        self.model = 'openai'
        self.logger = None
        self.billed_tokens = 0

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
        with open('prompt.md', 'r') as file:
            body = file.read()
        return f'{body} \n####\n{text}'
        # return MY_INVOICE_EXTRUDER_TMPL.replace('{context_str}', document) 
