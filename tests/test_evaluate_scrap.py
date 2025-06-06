import pathlib
from src.content_enhancer import ContentEnhancer
from src.helpers.np_helper import save_json
from src.md_embeddings import MarkdownEmbeddingGenerator
from src.blog_scraper import BlogScraper
from src.tag_extractor import TagExtractor
from src.md_clustering import ContentClustering
import os
import unittest
import unittest.async_case
import logging

from src.tag_analyzer import TagAnalyzer

TEST_DIR = pathlib.Path(__file__).parent


class TestRunScrape(unittest.async_case.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        # Configure logging
        # logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger('RunScrape')
        self.logger.setLevel(logging.DEBUG)
        for h in self.logger.handlers[:]:
            self.logger.removeHandler(h)
            h.close()
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(
            logging.Formatter('%(asctime)s %(levelname)s - %(filename)s:%(lineno)d - %(message)s')
        )
        self.logger.addHandler(console_handler)

        return super().setUp()

    def test_scrape_invoicer(self):
        blog_url = 'https://invoicer.blogspot.com'
        output_directory = os.path.join('c:\\git\\prompts', 'scraped', 'invoicer_blogspot')

        scraper = BlogScraper(self.logger, blog_url, output_directory)
        self.assertTrue(scraper is not None)
        self.assertEqual(scraper.scrape_blog(), 30)

    def test_scrape_poznajmadar(self):
        blog_url = 'https://poznajmadar.blogspot.com'
        output_directory = os.path.join('c:\\git\\prompts', 'scraped', 'poznaj_madar')

        scraper = BlogScraper(self.logger, blog_url, output_directory)
        self.assertEqual(scraper.scrape_blog(), 10)

    def test_extract_content(self):
        url = 'https://poznajmadar.blogspot.com/2017/03/kg-ksiegowanie-do-ksiegi-gownej.html'
        # url='http://invoicer.blogspot.com/2024/12/ai-nowa-funkcjonalnosc-jeden-plik-wiele.html'
        # url = 'https://poznajmadar.blogspot.com/2025/03/jak-uzyskac-wydruk-przysugujacych-i.html#comment-form'
        output_directory = os.path.join('c:\\git\\prompts', 'scraped', 'test')
        scraper = BlogScraper(self.logger, '', output_directory)
        post_html = scraper.fetch_page(url)
        md = scraper.extract_content(post_html, url)
        self.assertTrue(md is not None)

    def test_process_tags_poznajmadar(self):
        input_directory = pathlib.Path('c:/git/prompts/scraped/poznaj_madar')
        extractor = TagExtractor(self.logger)
        map = extractor.process_directory(input_directory / 'blog_posts')
        report = extractor.generate_yaml_report(map)  # Changed to generate_yaml_report

        os.makedirs(os.path.join(input_directory, 'report'), exist_ok=True)
        with open(input_directory / 'report' / 'tag-report.json', 'w', encoding='utf-8') as f:
            f.write(report)

    async def test_tag_analyse_poznajmadar(self):
        input_directory = pathlib.Path('c:/git/prompts/scraped/poznaj_madar')
        analyzer = TagAnalyzer(self.logger, input_directory)
        analyzer.load_tag_report()

        tags = analyzer.get_unique_tags()
        analyzer.generate_contents(tags)

        # definition = analyzer.process_tag('CRM')
        # definitions = {'CRM': definition}
        definitions = await analyzer.process_tags(tags)
        save_json(definitions, input_directory / 'report' / 'tag-definitions.json')

    async def test_embedding(self):
        input_directory = pathlib.Path('c:/git/prompts/scraped/poznaj_madar')

        generator = MarkdownEmbeddingGenerator(self.logger)
        await generator.process_directory(input_directory / 'blog_posts')
        generator.save_embeddings_to_json(input_directory / 'report' / 'embeddings.json')

    def test_clustering(self):
        input_directory = pathlib.Path('c:/git/prompts/scraped/poznaj_madar')

        generator = ContentClustering(self.logger)
        generator.load_embeddings_from_json(input_directory / 'report' / 'embeddings.json')
        clusters = generator.perform_clustering(n_clusters=10)
        save_json(clusters, input_directory / 'report' / 'cluster.json')

        generator.visualize_clusters(clusters, input_directory / 'report' / 'cluster')

        similar_docs = generator.find_similar_documents(3)
        self.assertIsNotNone(similar_docs)
        combined_documents = generator.linked_documents(similar_docs)
        save_json(combined_documents, input_directory / 'report' / 'linked.json')

    async def test_content_enhancer(self):
        input_directory = pathlib.Path('c:/git/prompts/scraped/poznaj_madar')
        generator = ContentEnhancer(self.logger, input_directory)
        await generator.process_files()
        self.assertTrue(True)
