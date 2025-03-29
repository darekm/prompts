import asyncio
import os
from datetime import datetime
from typing import Optional

import httpx


class EmbeddingConnectorException(Exception):
    def __init__(self, code, message) -> None:
        self.code = code
        self.message = message
        super().__init__(f'Error {code}:{message}')


class EmbeddingConnector:
    def __init__(self, logger) -> None:
        self.logger = logger
        self.last_response = None
        self.client = httpx.AsyncClient()
        
        # Default to Gemini embedding model
        self.init_gemini4()

    def init_model(self, model):
        if model == 'gemini' or model is None:
            self.init_gemini()
        elif model == 'google':
            self.init_gemini4()
        elif model == 'openai':
            self.init_openai()
        elif model == 'azure':
            self.init_azure()
        else:
            self.init_gemini()  # Default to Gemini if model type is unknown

    def init_gemini(self):
        self.model = 'gemini-embedding-exp-03-07'
        self.api_key = os.getenv('GOOGLE_API_KEY')
        if self.api_key is None:
            raise ValueError('GOOGLE_API_KEY is not set.')
        
        self.api_url = f'https://generativelanguage.googleapis.com/v1beta/models/{self.model}:embedContent?key={self.api_key}'
        self.headers = {
            'content-type': 'application/json',
        }
        self.task_type = 'SEMANTIC_SIMILARITY'
    def init_gemini4(self):
        self.model= 'text-embedding-004'
        self.api_key = os.getenv('GOOGLE_API_KEY')
        if self.api_key is None:
            raise ValueError('GOOGLE_API_KEY is not set.')
        
        self.api_url = f'https://generativelanguage.googleapis.com/v1beta/models/{self.model}:embedContent?key={self.api_key}'
        self.headers = {
            'content-type': 'application/json',
        }
        self.task_type = ''

    def init_openai(self):
        self.model = 'text-embedding-3-small'
        self.api_key = os.getenv('OPENAI_API_KEY')
        if self.api_key is None:
            raise ValueError('OPENAI_API_KEY is not set.')
        
        self.api_url = 'https://api.openai.com/v1/embeddings'
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-type': 'application/json'
        }
        self.task_type = None

    def init_azure(self):
        self.model = 'text-embedding-ada-002'
        self.api_key = os.getenv('AZURE_OPENAI_KEY')
        self.endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
        if self.api_key is None or self.endpoint is None:
            raise ValueError('AZURE_OPENAI_KEY or AZURE_OPENAI_ENDPOINT is not set.')
        
        self.api_url = f'{self.endpoint}/openai/deployments/{self.model}/embeddings?api-version=2023-05-15'
        self.headers = {
            'api-key': self.api_key,
            'Content-Type': 'application/json'
        }
        self.task_type = None

    def embed_sync(self, text: str) -> str:
        """Synchronous wrapper for the async embedding method"""
        return asyncio.run(self.embed(text))

    async def embed(self, text: str) -> str:
        """Compute an embedding for the input text"""
        start = datetime.now()
        
        json_data = {}
        if 'gemini' in self.model:
            json_data = {
                "model": f"models/{self.model}",
                "content": {
                    "parts": [{"text": text}]
                },
                "taskType": self.task_type
            }
        elif 'text-embedding-004' in self.model:
            json_data = {
                "model": f"models/{self.model}",
                "content": {
                    "parts": [{"text": text}]
                },
            }
        elif 'openai' in self.api_url:
            json_data = {
                "model": self.model,
                "input": text,
                "encoding_format": "float"
            }
        elif 'azure' in self.api_url:
            json_data = {
                "input": text
            }
        
        response = await self.client.post(
            self.api_url, 
            json=json_data, 
            headers=self.headers, 
            timeout=60
        )
        
        duration = (datetime.now() - start).total_seconds()
        
        if response.status_code != 200:
            self.logger.error(f'{self.model} embedding error code={response.status_code} {response.text}')
            raise EmbeddingConnectorException(
                response.status_code, 
                f'{self.model} embedding len={len(text)} duration: {duration}'
            )
        
        json_response = response.json()
        self.last_response = json_response
        
        # Extract embedding based on API response structure
        embedding = self.extract_embedding(json_response)
        
        # Log embedding computation details
        embedding_length = len(embedding) if embedding is not None else 0
        
        self.logger.debug(
            f'{self.model} embedding dims={embedding_length},  duration={duration:.2f}s'
        )
        
        return embedding

    def batch_embed_sync(self, texts: list) -> list:
        """Synchronous wrapper for batch embedding"""
        return asyncio.run(self.batch_embed(texts))

    async def batch_embed(self, texts: list) -> list:
        """Process multiple texts and return their embeddings"""
        embeddings = []
        for text in texts:
            embedding = await self.embed(text)
            embeddings.append(embedding)
        return embeddings

    def extract_embedding(self, response):
        """Extract embeddings from API response based on provider format"""
        if 'embedding' in response:  # Gemini format
            return response['embedding']['values']
        elif 'data' in response:  # OpenAI format
            return response['data'][0]['embedding']
        
        self.logger.error(f"Unknown embedding response format: {response}")
        return None

