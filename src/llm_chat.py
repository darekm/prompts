import asyncio
import pathlib

from src.helpers.chat_connector import ChatConnector

PROMPT_DIR = pathlib.Path(__file__).parent.parent


class ChatPrompt:
    def __init__(self, logger):
        self.model = 'openai41'
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

    async def extract_fk(self, text):
        # self.logger.debug(f'Completion  {model}  invoice')
        result = await self.completion(self.prompt('rejestry_vat.md', text), self.model)
        return result

    async def extract(self, variant, text):
        self.logger.debug(f'Completion  {self.model}  {variant}')
        result = await self.completion(self.prompt(variant, text), self.model)
        return result

    def file(self, name):
        with open(self.path / name, 'r',encoding='utf-8') as file:
            body_system = file.read()
        return body_system

    def reports(self, name):
        if name == 'kadry':
            reports = self.file('report_koniec_umow.md')
            report_umpra=self.file('report_umpra.json')
            report_badania = self.file('report_badania.json')
            return f'\f# **attached_reports**\n{reports} ## **baza_umów_pracowniczych**\n{report_umpra} ## **baza_badań**\n{report_badania}'
        if name == 'place':
            reports = self.file('report_place.md')
            return f'\f# **Raporty**\n{reports} '
        if name == 'vat':
            with open(self.path / 'vat_report.md', 'r') as file:
                reports = file.read()
            return f'\f# **Raporty**\n{reports} '

        with open(self.path / 'instrukcja_rejestry_vat.md', 'r') as file:
            instrukcja_rejestry = file.read()

        with open(self.path / 'base_report.md', 'r') as file:
            reports = file.read()
        return f'\f# **Instrukcje**\n {instrukcja_rejestry} \f# **Raporty**\n{reports} '

    def prompt(self, variant, question):
        if variant == 'kadry':
            return f'{self.file("primary_chat.md")} {self.reports(variant)}\f# **Pytania** \n{question}'

        return f'{self.file("system_chat.md")} {self.reports(variant)}\f# **Pytania** \n{question}'
