import asyncio
import os
import re
import json
import aiohttp
from datetime import datetime

import httpx

from src.helpers.string_helper import find_between


class ConnectorInsufficientQuota(Exception):
    def __init__(self, model, code, message) -> None:
        self.code = code
        self.message = message
        super().__init__(f'Error {model} Insufficient Quota {code}:{message}')


class ConnectorException(Exception):
    def __init__(self, code, message) -> None:
        self.code = code
        self.message = message
        super().__init__(f'Error {code}:{message}')


class ChatConnector:
    def __init__(self, logger, verbose=False) -> None:
        self.logger = logger
        self.response_format = False
        self.billed_tokens = 0
        self.no_stream = False
        self.last_response = None
        self.verbose = verbose
        self.thinking = False
        self.reset()
        self.system_role = False
        self.extract_json = False
        self.google = False
        self.client = httpx.AsyncClient()
        
        self.initOpenAI4o()

    async def close(self):
        if self.client:
            #await self.client.close()
            self.client = None
        self.reset()

    def reset(self):
        self.system_role = False
        self.extract_json = True
        self.google = False
        self.claude = False
        self.response_format = False


    def init_model(self, model):
        if model == 'claude':
            self.initAntrophic()
        if model == 'google':
            self.initGemini15Flash()
        if model == 'together':
            self.initTogether('ll')
        if model == 'gemini':
            self.initGemini25Flash()
        if model == 'o1-mini':
            self.initOpenAIo1()
        if model == '4o-mini':
            self.initOpenAI4omini()
        if model == 'o3-mini':
            self.initOpenAIo3mini()
        if model == 'openai':
            self.initOpenAI4o()
        if model == 'openai4o':
            self.initOpenAI4o()
        if model == 'openai41nano':
            self.initOpenAI41('gpt-4.1-nano')
        if model == 'openai41mini':
            self.initOpenAI41('gpt-4.1-mini')
        if model == 'openai41':
            self.initOpenAI41('gpt-4.1')
        if model == 'phi4':
            self.initAzurePhi4()

    def initOpenAI4o(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        if self.api_key is None:
            raise ValueError('OPENAI_API_KEY key is not set. ')

        self.api_url = 'https://api.openai.com/v1/chat/completions'
        self.headers = {'Authorization': f'Bearer {self.api_key}', 'Content-type': 'application/json'}
        self.model = 'gpt-4o'
        self.response_format = True
    def initOpenAI41(self, model):
        self.reset()
        self.api_key = os.getenv('OPENAI_API_KEY')
        if self.api_key is None:
            raise ValueError('OPENAI_API_KEY key is not set. ')

        self.api_url = 'https://api.openai.com/v1/responses'
        self.headers = {'Authorization': f'Bearer {self.api_key}', 'Content-type': 'application/json'}

        self.model = model
        self.response_format = 'json'
        self.system_role = 'responses'
        self.extract_json = True

    def initOpenAI4omini(self):
        self.reset()
        self.api_key = os.getenv('OPENAI_API_KEY')
        if self.api_key is None:
            raise ValueError('OPENAI_API_KEY key is not set. ')

        self.api_url = 'https://api.openai.com/v1/chat/completions'
        self.headers = {'Authorization': f'Bearer {self.api_key}', 'Content-type': 'application/json'}
        self.model = 'gpt-4o-mini'
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
    
    def initOpenAIo3mini(self):
        self.reset()
        self.api_key = os.getenv('OPENAI_API_KEY')
        if self.api_key is None:
            raise ValueError('OPENAI_API_KEY key is not set. ')

        self.api_url = 'https://api.openai.com/v1/chat/completions'
        self.headers = {'Authorization': f'Bearer {self.api_key}', 'Content-type': 'application/json'}
        self.model = 'o3-mini'
        self.extract_json = True
        self.response_format = False

    def initAntrophic(self, model='claude-3-5-sonnet-20240620'):
        self.reset()
        self.system_role = 'external'
        self.response_format = False
        self.model = model
        self.claude = True
        self.extract_json = True
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

    def initGemini15Flash(self):
        self.model = 'google'
        self.response_format = False
        self.api_key = os.getenv('GOOGLE_API_KEY')
        self.google = True
        self.api_url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={self.api_key}'
        self.headers = {
            'content-type': 'application/json',
        }

    def initGemini20Flash(self):
        self.reset()
        self.model = 'gemini'
        self.response_format = False
        self.api_key = os.getenv('GOOGLE_API_KEY')
        self.google = True
        self.api_url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={self.api_key}'
        self.headers = {
            'content-type': 'application/json',
        }

    def initGemini25Flash(self):
        self.reset()
        self.model = 'gemini'
        self.extract_json = True
        self.api_key = os.getenv('GOOGLE_API_KEY')
        self.google = True
        # self.api_url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-04-17:generateContent?key={self.api_key}'
        self.api_url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.api_key}'
        self.headers = {
            'content-type': 'application/json',
        }
    def initAzurePhi4(self):
        self.reset()
        self.model = 'Phi-4'
        self.extract_json = True
        self.api_key = os.getenv('GITHUB_API_KEY')
        self.api_url = 'https://models.inference.ai.azure.com/chat/completions'
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}',
        }

    def initTogether(self, model: str):
        self.reset()
        self.model = model
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
    async def ask_safe(self, user_content: str) -> str:
        #self.client = aiohttp.ClientSession()
        try:
            return await self.ask(user_content)
        finally:
            await self.close()
        # Save the result to a file or database

    async def ask(self, user_content: str) -> str:
        messages = [{'role': 'user', 'content': user_content}]
        json_data = {'messages': messages, 'temperature': 0.01, 'max_tokens': 16380}
        if self.system_role == 'responses':
            json_data = {
                'input': user_content,
                'temperature': 0.01,
                'model': self.model,
            }
        if self.model:
            json_data['model'] = self.model
        if self.no_stream:
            json_data['stream'] = False
        if self.extract_json:
            if self.response_format == 'json':
                json_data['text'] = {'format': {'type': 'json_object'}}
            elif self.response_format:
                json_data['response_format'] = {'type': 'json_object'}
        if self.system_role == 'external':
            json_data['messages'] = [{'role': 'user', 'content': user_content}]
            # json_data['system'] = self.system_text
        if (self.model == 'o1-mini') or (self.model == 'o3-mini'):
            del json_data['temperature']
            del json_data['max_tokens']
        if self.model == 'o3-mini':
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
            if not self.thinking:
                json_data['generationConfig']['thinkingConfig'] = {'thinkingBudget': 0}
        # print(json_data)
        start = datetime.now()

        response = await self.client.post(self.api_url, json=json_data, headers=self.headers, timeout=180)
        _duration = (datetime.now() - start).total_seconds()
        # self.logger.debug(
        #    f'{self.model} ask len={len(user_content)} response code={response.status_code} len={len(response.text)}  duration: {_duration}'
        # )
        if response.status_code == 529:
            return f'{"error":"529","message":"{response.text}"}'
        if response.status_code == 429:
            self.logger.error(f'{self.model} ask error code={response.status_code} {response.text}')
            raise ConnectorInsufficientQuota(self.model, 429, 'Too many requests')
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
    async def ask_json(self, user_content: str) -> dict:
        self.extract_json = True
        s = await self.ask(user_content)
        return json.loads(s)

    async def ask_text(self, user_content: str) -> dict:
        self.client = aiohttp.ClientSession()
        try:
            self.extract_json = False
            s = await self.ask(user_content)
            return s
        finally:
            await self.close()

    def get_usage(self, completion):
        if completion.get('usage'):
            return completion['usage']
        if completion.get('usageMetadata'):
            return completion['usageMetadata']
        return None

    def get_text(self, completion):
        if completion.get('candidates'):  # google
            if completion['candidates'][0]['finishReason'] == 'MAX_TOKENS':
                raise ConnectorException(701, 'The generated exceed max content')
            if completion['candidates'][0]['finishReason'] == 'OTHER':
                raise ConnectorException(701, 'The generated stopped for other reason')
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
                raise ConnectorException(701, 'The geneerated exceed max content')

            j = str(completion['content'][0]['text'])
            result = find_between(j, '```json', '```')
            return result
        if completion.get('output'):  # openai responses
            output = completion['output'][0]
            if output['status'] != 'completed':
                raise ConnectorException(701, f'The generated content is {output["status"]}')
            text = output['content'][0]['text']
            if self.extract_json:
                extracted = find_between(text, '```json', '```')
                if not extracted:
                    extracted = text
            return extracted

        if completion.get('message'):
            return str(completion['message']['content'])
        text = completion['choices'][0]  # OpenAi
        if text['finish_reason'] == 'content_filter':
            raise ConnectorException(701, 'The generated content is filtered')
        if text['finish_reason'] == 'length':
            raise ConnectorException(701, 'The generated content is too long')
        text = text['message']['content']
        if self.extract_json:
            text2 = find_between(text, '```json', '```')
            if text2:
                text = text2
        return text

    def get_total_tokens(self, usage):
        us = usage.get('input_tokens', None)
        if us:
            return us + usage.get('output_tokens', 0)
        return usage.get('totalTokenCount', usage.get('total_tokens', 0))
