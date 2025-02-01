import asyncio
import os
import re
from datetime import datetime

import httpx

from src.helpers.string_helper import find_between


class ConnectorException(Exception):
    def __init__(self, code, message) -> None:
        self.code = code
        self.message = message
        super().__init__(f'Error {code}:{message}')


class ChatConnector:
    def __init__(self, logger) -> None:
        self.logger = logger
        self.response_format = False
        self.billed_tokens = 0
        self.no_stream = False
        self.last_response = None
        self.system_role = False
        self.extract_json = False
        self.google = False
        self.client = httpx.AsyncClient()
        self.system_text = ' You are an expert in extraction information from given context.\n'
        'Always answer the query using the provided context information and not prior knowledge.\n'

        self.initOpenAI4o()

    def init_model(self, model):
        if model == 'claude':
            self.initAntrophic()
        if model == 'google':
            self.initGoogle()
        if model == 'together':
            self.initTogether('ll')
        if model == 'gemini':
            self.initGemini20Fash()
        if model == 'o1-mini':
            self.initOpenAIo1()
        if model == '4o-mini':
            self.initOpenAI4omini()
        if model == 'openai':
            self.initOpenAI4o()
        if model == 'openai4o':
            self.initOpenAI4o()
        if model == 'phi4':
            self.initAzurePhi4()

    def initOpenAI4omini(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        if self.api_key is None:
            raise ValueError('OPENAI_API_KEY key is not set. ')

        self.api_url = 'https://api.openai.com/v1/chat/completions'
        self.headers = {'Authorization': f'Bearer {self.api_key}', 'Content-type': 'application/json'}
        self.model = 'gpt-4o-mini'
        self.response_format = True
    def initOpenAI4o(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        if self.api_key is None:
            raise ValueError('OPENAI_API_KEY key is not set. ')

        self.api_url = 'https://api.openai.com/v1/chat/completions'
        self.headers = {'Authorization': f'Bearer {self.api_key}', 'Content-type': 'application/json'}
        self.model = 'gpt-4o'
        self.response_format = True

    def initOpenAIo1(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        if self.api_key is None:
            raise ValueError('OPENAI_API_KEY key is not set. ')

        self.api_url = 'https://api.openai.com/v1/chat/completions'
        self.headers = {'Authorization': f'Bearer {self.api_key}', 'Content-type': 'application/json'}
        self.model = 'o1-mini'
        self.extract_json = True
        self.response_format = False

    def initAntrophic(self, model='claude-3-5-sonnet-20240620'):
        self.system_role = 'external'
        self.response_format = False
        self.model = model
        self.api_key = os.getenv('ANTHROPIC_API_KEY')
        if self.api_key is None:
            raise ValueError('ANTHROPIC_API_KEY key is not set. ')
        self.api_url = 'https://api.anthropic.com/v1/messages'
        self.headers = {
            'x-api-key': self.api_key,
            'content-type': 'application/json',
            'anthropic-version': '2023-06-01',
            'anthropic-beta': 'prompt-caching-2024-07-31',
        }

    def initGoogle(self):
        self.model = 'google'
        self.response_format = False
        self.api_key = os.getenv('GOOGLE_API_KEY')
        self.google = True
        self.api_url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={self.api_key}'
        self.headers = {
            'content-type': 'application/json',
        }

    def initGemini20Fash(self):
        self.model = 'gemini'
        self.response_format = False
        self.api_key = os.getenv('GOOGLE_API_KEY')
        self.google = True
        self.api_url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={self.api_key}'
        self.headers = {
            'content-type': 'application/json',
        }

    def initAzurePhi4(self):
        self.model = 'Phi-4'
        self.response_format = False
        self.extract_json = True
        self.api_key = os.getenv('GITHUB_API_KEY')
        self.api_url = 'https://models.inference.ai.azure.com/chat/completions'
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}',
        }

    def initTogether(self, model: str):
        self.model = model
        self.response_format = False
        self.api_key = os.getenv('TOGETHER_API_KEY')
        self.api_url = 'https://api.together.xyz/v1/chat/completions'
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'content-type': 'application/json',
            'accept': 'application/json',
        }

    def ask_sync(self, user_content: str) -> str:
        asyncio.run(self.ask(user_content))
        return self.last_text

    async def ask(self, user_content: str) -> str:
        # messages = [{'role': 'system', 'content': self.system_text}, {'role': 'user', 'content': user_content}]
        messages = [{'role': 'user', 'content': user_content}]
        json_data = {'messages': messages, 'temperature': 0.01, 'max_tokens': 16000}
        if self.model:
            json_data['model'] = self.model
        if self.no_stream:
            json_data['stream'] = False
        if self.response_format:
            json_data['response_format'] = {'type': 'json_object'}
        if self.system_role == 'external':
            json_data['messages'] = [{'role': 'user', 'content': user_content}]
            json_data['system'] = self.system_text
        if self.model == 'o1-mini':
            del json_data['temperature']
            del json_data['max_tokens']
        if self.model == 'Phi-4':
            json_data = {
                'messages': messages,
                'temperature': 1.0,
                # 'topK': 0,
                'top_p': 1.0,
                'max_tokens': 8192,
                'model': 'Phi-4',
                'repetition_penalty': 1,
                # 'responseMimeType': 'text/plain',
            }
        if self.google:
            json_data = {
                'contents': [{'parts': [{'text': user_content}]}],
                'generationConfig': {
                    'temperature': 0,
                    'topK': 40,
                    'topP': 0.95,
                    'maxOutputTokens': 8192,
                    'responseMimeType': 'text/plain',
                },
            }
        # print(json_data)
        start = datetime.now()

        response = await self.client.post(self.api_url, json=json_data, headers=self.headers, timeout=180)
        _duration = (datetime.now() - start).total_seconds()
        # self.logger.debug(
        #    f'{self.model} ask len={len(user_content)} response code={response.status_code} len={len(response.text)}  duration: {_duration}'
        # )
        if response.status_code == 529:
            return f'{"error":"529","message":"{response.text}"}'
        if response.status_code != 200:
            self.logger.error(f'{self.model} ask error code={response.status_code} {response.text}')
            raise ConnectorException(
                response.status_code, f'{self.model} ask len={len(user_content)} duration: {_duration}'
            )

        _json = response.json()
        self.last_response = _json
        self.logger.debug(str(_json))
        self.billed_tokens = self.get_total_tokens(self.get_usage(_json))
        self.logger.debug(
            f' {self.model} duration: {_duration} billed: {self.billed_tokens} usage{self.get_usage(_json)}'
        )
        self.last_text = self.get_text(_json)
        return self.last_text

    def get_usage(self, completion):
        if completion.get('usage'):
            return completion['usage']
        if completion.get('usageMetadata'):
            return completion['usageMetadata']
        return None

    def get_text(self, completion):
        if completion.get('candidates'):  # google
            jj = str(completion['candidates'][0]['content']['parts'][0]['text'])
            j = find_between(jj, '```json', '```')
            if not j:
                j = jj
            j = j.strip()
            if not j:
                return ''
            if j[0] == '[':
                j = j[1:-1]

            result = re.sub(r'(?<!\\)\\(?!["\\/bfnrt]|u[0-9a-fA-F]{4})', r'', j)
            return result

        if completion.get('content'):  # Anthropic
            if completion.get('stop_reason') == 'max_token':
                raise ConnectorException(701, 'The geneerated  exceed max content')

            j = str(completion['content'][0]['text'])
            result = find_between(j, '```json', '```')
            return result

        if completion.get('message'):
            return str(completion['message']['content'])
        text = completion['choices'][0]  # OpenAi
        if text['finish_reason'] == 'content_filter':
            raise ConnectorException(701, 'The generated content is filtered')
        if text['finish_reason'] == 'length':
            raise ConnectorException(701, 'The generated content is too long')
        text = text['message']['content']
        if self.extract_json:
            text = find_between(text, '```json', '```')
        return text

    def get_total_tokens(self, usage):
        return usage.get('totalTokenCount', usage.get('total_tokens', 0))
