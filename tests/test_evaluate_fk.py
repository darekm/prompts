import pathlib

from tests.evaluate_chat import EvaluateChat, properly

TEST_DIR = pathlib.Path(__file__).parent


class TestChatFKEvaluate(EvaluateChat):
    reg = None

    def setUp(self) -> None:
        super().setUp()
        self.path = 'data_fk'
        self.test_dir = TEST_DIR
        return

    @properly(False)
    async def test_ile_godzin(self):
        await self.check_question(
            'ilegodzin', 'place', 'Ile wykorzystano urlopu siła wyższa?', {'value': 0, 'genre': 'data'}
        )

    async def test_explain(self):
        await self.explain_response('ilegodzin', 'value should be `unknown` but LLM response 4')
        return

    async def test_wielkosc_sprzedazy(self):
        await self.check_question(
            'wielkoscsprzedazy', 'vat', 'Podaj wielkość sprzedaży?', {'value': 123344.00, 'genre': 'data'}
        )

    async def test_wysokość_vat(self):
        await self.check_question(
            'wysokoscvat', 'syntetyka', 'Podaj wysokość VAT?', {'value': 123344.00, 'genre': 'data'}
        )
    async def test_podatek_dozaplaty(self):
        await self.check_question(
            'podatekdozaplaty', 'syntetyka', ' Jaka jest wysokość podatku do zapłacenia za listopad?', {"period": "from 01.11.2025 to 30.11.2025", 'genre': 'clarification'}
        )
