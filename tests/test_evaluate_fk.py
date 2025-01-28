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
    async def test_faktura_korygujaca_atman(self):
        await self.check_question('fk.md', 'Ile godzin pracował pracownik?', {'value': 8})
