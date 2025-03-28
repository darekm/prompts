import pathlib
from src.blog_scraper import BlogScraper
from src.yaml_processor import YamlProcessor
import os
import unittest
import logging

from src.tag_analyzer import TagAnalyzer

TEST_DIR = pathlib.Path(__file__).parent


class TestRunScrape(unittest.TestCase):
    def setUp(self) -> None:
        # Configure logging
        #logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
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
        url='https://poznajmadar.blogspot.com/2017/03/kg-ksiegowanie-do-ksiegi-gownej.html'
        #url='http://invoicer.blogspot.com/2024/12/ai-nowa-funkcjonalnosc-jeden-plik-wiele.html' 
        #url = 'https://poznajmadar.blogspot.com/2025/03/jak-uzyskac-wydruk-przysugujacych-i.html#comment-form'
        output_directory = os.path.join('c:\\git\\prompts', 'scraped', 'test')
        scraper = BlogScraper(self.logger, '', output_directory)
        post_html = scraper.fetch_page(url)
        md = scraper.extract_content(post_html,url)
        self.assertTrue(md is not None)

    def test_process_tags_poznajmadar(self):
        input_directory = pathlib.Path("c:/git/prompts/scraped/poznaj_madar")
        map = YamlProcessor.process_directory(input_directory / 'blog_posts')
        #report= YamlProcessor.generate_yaml_report(map)
        report= YamlProcessor.generate_json_report(map)
    
        os.makedirs(os.path.join(input_directory, "report"), exist_ok=True)
        with open(input_directory / 'report' / 'tag-report.json', 'w', encoding='utf-8') as f:
            f.write(report)

    

    def test_tag_analyse_poznajmadar(self):
        input_directory = pathlib.Path("c:/git/prompts/scraped/poznaj_madar")
        json_report_file=input_directory / 'report' / 'tag-report.json'
        analyzer = TagAnalyzer(self.logger, json_report_file, input_directory)
        analyzer.load_json_data()
        
        tags = analyzer.get_unique_tags()
        
        definition = analyzer.process_tag('CRM')
        definitions={'CRM': definition}
        analyzer.save_tags(definitions)
        
        