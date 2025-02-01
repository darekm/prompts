import asyncio
import pathlib

from src.helpers.chat_connector import ChatConnector

PROMPT_DIR = pathlib.Path(__file__).parent.parent


class ChatPrompt:
    def __init__(self, logger):
        self.model = 'openai4o'
        self.logger = logger
        self.billed_tokens = 0
        self.full_prompt = ''
        self.path = PROMPT_DIR / 'prompt'

    async def completion(self, prompt, model):
        self.full_prompt = prompt
        chat = ChatConnector(self.logger)
        chat.init_model(model)
        await asyncio.sleep(0.1)
        response = await chat.ask(prompt)
        self.billed_tokens += chat.billed_tokens
        return response

    async def explain(self, text, result):
        with open(self.path / 'explain.md', 'r') as file:
            explain_prompt = file.read()
        res = await self.completion(f'{explain_prompt} {text} {result}  ', self.model)
        return res

    async def extract(self, variant, text):
        if variant == 'place':
            return await self.extract_place(text, variant)
        return await self.extract_fk(text)

    async def extract_fk(self, text):
        # self.logger.debug(f'Completion  {model}  invoice')
        result = await self.completion(self.prompt('rejestry_vat.md', text), self.model)
        return result

    async def extract_place(self, text, model):
        # self.logger.debug(f'Completion  {model}  invoice')
        result = await self.completion(self.prompt('place', text), self.model)
        return result

    def system_chat(self):
        with open(self.path / 'system_chat.md', 'r') as file:
            body_system = file.read()
        return body_system

    def reports(self, name):
        if name == 'place':
            with open(self.path / 'place_report.md', 'r') as file:
                reports = file.read()
            return f'\f# **Raporty**\n{reports} '

        with open(self.path / name, 'r') as file:
            rejestry = file.read()
        rejestry = ''

        with open(self.path / 'base_report.md', 'r') as file:
            reports = file.read()
        return f'\f# **Instrukcje**\n {rejestry} \f# **Raporty**\n{reports} '

    def prompt(self, name, question):
        return f'{self.system_chat()} {self.reports(name)}\f# **Pytania** \n{question}'
