import json
import os
import unittest
import unittest.async_case
from datetime import datetime

from sqlalchemy import false

from llm_chat import ChatPrompt
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
        self.short = os.environ.get('SHORT', '0')
        self.error_fields = []

        return super().setUp()

    @classmethod
    def setUpClass(cls):
        # evaluate_ladder.init(cls.__name__)
        return super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        # evaluate_ladder.store()
        pass

    def eprint(self, key, s):
        self.err += f'{key}::{s}'
        self.error_fields.append(key)
        # self.logger.error(f'Errorcheck in {self._json_name} for {key}::{s}')

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
            if _left == false and _right == '':
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

    def check(self, json_name, record):
        self.err = ''
        self.error_fields = []
        self._json_name = json_name
        with open(f'{os.path.join(self.test_dir, self.path, json_name)}.json', 'r', encoding='utf-8') as file:
            s = file.read()
            filejson = json.loads(s)
        invoice = json.loads(record['invoice'])
        count = 0

        errors = 0
        self.prompt = invoice.get('prompt', '')

        for key in filejson:
            if key[0] == '_':
                continue
            count += 1
            good = self.check_instance(filejson[key], invoice.get(key))

            if not good:
                self.eprint(key, f'{filejson[key]}!={invoice.get(key)}')
            else:
                errors += 1
        return errors, count

    async def compute_document(self, file_name, question, extension):
        record = ChatPrompt().extract_fk(question, extension)
        self.dump(file_name, record)
        return record

    async def check_question(self, file_name, question, extension):
        start = datetime.now()

        _ladder = {}
        _ladder['file_name'] = question
        _ladder['extension'] = extension
        self._json_name = file_name

        try:
            record = await self.compute_document(file_name, question, extension)
            _ladder['duration'] = (datetime.now() - start).total_seconds()

            proper, count = self.check(file_name, record)
            _ladder['error_fields'] = self.error_fields
            _ladder['errors'] = count - proper
            _ladder['count'] = count
            _ladder['proper'] = proper
            _ladder['prompt'] = self.prompt
            _ladder['tokens'] = record.get('billed_tokens', 0)

        finally:
            pass
        self.assertEqual(proper, count, f' Errors in {file_name}')
