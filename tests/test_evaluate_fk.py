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
        await self.check_question('ilegodzin', 'Ile godzin pracował pracownik?', {'period': "none","genre":"data"})
