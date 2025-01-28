import pathlib

from tests.evaluate_chat import EvaluateCase, properly

TEST_DIR = pathlib.Path(__file__).parent


class TestChatFKEvaluate(EvaluateCase):
    reg = None

    def setUp(self) -> None:
        super().setUp()
        self.path = 'data_fk'
        self.test_dir = TEST_DIR
        return

    async def compute_document(self, file_name, extension):
        meta = {
            'id': '1',
            'doc_no': file_name,
            'doc_id': f'DOCUM{1}-{file_name}',
            'space': 'test',
        }
        file_body = self.load_pdf(f'{file_name}{extension}')
        record = await self.ask_chat(file_body, f'{file_name}{extension}', meta)
        self.dump(file_name, record)
        return record

    async def check_invoice(self, file_name):
        await self.check_document(file_name, 'invoice', '.pdf')

    async def check_correction(self, file_name):
        await self.check_document(file_name, 'invoice_correction', '.pdf')

    async def check_payroll_html(self, file_name):
        await self.check_document(file_name, 'bank', '.htm')

    @properly(False)
    async def test_ile_godzin(self):
        await self.check_chat('Ile pozosotało godzin', '8')

   