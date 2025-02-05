import json
import os
import unittest
import unittest.async_case
from datetime import datetime

import logging
from src.llm_chat import ChatPrompt
from src.helpers.string_helper import string2float


def properly(condition):
    def decorator(test_func):
        if (condition == 'LONG') and (os.environ.get('SHORT', '0') in ['1', '2']):
            return unittest.skip('custom condition met')(test_func)
        if (os.environ.get('SHORT', '0') == '1') and condition:
            return unittest.skip('custom condition met')(test_func)
        if (os.environ.get('SHORT', '0') == '2') and not condition:
            return unittest.skip('custom condition met')(test_func)
        return test_func

    return decorator


class EvaluateChat(unittest.async_case.IsolatedAsyncioTestCase):
    test_dir = ''

    def setUp(self) -> None:
        self.err = ''
        self.prompt = ''
        self.path = ''
        self.debug_level= '2'
        self.short = os.environ.get('SHORT', '0')
        self.error_fields = []
        self.billed_tokens = 0
        self.setup_debug_logger()

        return super().setUp()

    @classmethod
    def setUpClass(cls):
        # evaluate_ladder.init(cls.__name__)
        return super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        # evaluate_ladder.store()
        pass

    def setup_debug_logger(self):
        # Setup a logger for debugging
        # logging.config.fileConfig('logger.dev.ini', disable_existing_loggers=False)
        self.logger = logging.getLogger('Prompts:')
        self.logger.setLevel(logging.DEBUG)
        for h in self.logger.handlers[:]:
            self.logger.removeHandler(h)
            h.close()
        console_handler = logging.StreamHandler()
        if self.debug_level == '2':
            console_handler.setLevel(logging.DEBUG)
        else:
            console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(
            logging.Formatter('%(asctime)s %(levelname)s - %(filename)s:%(lineno)d - %(message)s')
        )
        self.logger.addHandler(console_handler)
        self.unittest = True
        self.BLOB_SAS = os.environ.get('BLOB_SAS') or ''

    def eprint(self, key, s):
        self.err += f'{key}::{s}'
        self.error_fields.append(key)
        self.logger.error(f'Errorcheck in {self._json_name} for {key}::{s}')

    def shortdek(self):
        def decorator(test_func):
            if self.short:
                return unittest.skip('custom condition met')(test_func)
            return test_func

        return decorator

    def load_pdf(self, file_name):
        with open(os.path.join(self.test_dir, self.path, file_name), 'rb') as file:
            filebody = file.read()
        return filebody

    def compare(self, _left, _right) -> bool:
        if isinstance(_left, bool):
            if not _left and _right == '':
                return True
            return _left == _right
        if isinstance(_left, float) or isinstance(_left, int):
            return abs(_left - string2float(_right)) < 1e-5
        return _left == _right

    def dump(self, json_name, record):
        with open(f'{os.path.join(self.test_dir, self.path, json_name)}.json.out', 'w') as file:
            file.write(json.dumps(record))

    def check_instance(self, field, value):
        if isinstance(field, list):
            for i in range(len(field)):
                if self.compare(field[i], value):
                    return True
        elif isinstance(field, dict):
            if field == value:
                return True
            if field == {'any': True}:
                return value is not None
            for key in field:
                if not self.check_instance(field[key], value.get(key)):
                    return False
            return True
        else:
            if self.compare(field, value):
                return True
        return False

    def check(self, extension, record):
        self.err = ''
        self.error_fields = []
        response = json.loads(record)
        count = 0

        errors = 0
        # self.prompt = response.get('prompt', '')

        for key in extension:
            if key[0] == '_':
                continue
            count += 1
            good = self.check_instance(extension[key], response.get(key))

            if not good:
                self.eprint(key, f'{extension[key]}!={response.get(key)}')
            else:
                errors += 1
        return errors, count

    async def compute_document(self, file_out, question, variant):
        chat = ChatPrompt(self.logger)
        record = await chat.extract(variant,question)
        self.billed_tokens += chat.billed_tokens
        r={'prompt': chat.full_prompt, 'response': json.loads(record)}
        self.dump(file_out, r)
        return record
    
    async def compute_explain(self, file_out, error):
        with open(f'{os.path.join(self.test_dir, self.path, file_out)}.json.out', 'r') as file:
            body=file.read

        chat = ChatPrompt(self.logger)
        record = await chat.explain(body,error)
        self.billed_tokens += chat.billed_tokens
        self.dump(f'{file_out}.prompt', record)
        return record
    
    async def check_question(self, file_name, variant,question, answer):
        start = datetime.now()

        _ladder = {}
        _ladder['question'] = question
        _ladder['ground'] = answer
        self._json_name = file_name

        try:
            self.prompt = question
            record = await self.compute_document(f'{file_name}.out', question, variant)
            _ladder['duration'] = (datetime.now() - start).total_seconds()

            proper, count = self.check(answer, record)
            _ladder['error_fields'] = self.error_fields
            _ladder['errors'] = count - proper
            _ladder['count'] = count
            _ladder['proper'] = proper
            _ladder['prompt'] = self.prompt
            _ladder['tokens'] = self.billed_tokens

        finally:
            pass
        self.assertEqual(proper, count, f' Errors in {file_name}')


    async def explain_response(self, file_name, error):
        record = await self.compute_explain(f'{file_name}.out', error)
        print( record)
        self.assertTrue(record, f' Errors in {file_name}')

           