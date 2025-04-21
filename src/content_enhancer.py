import os
import json
import re
from typing import List
import markdown
from bs4 import BeautifulSoup
import glob
import csv
from datetime import datetime

from src.helpers.np_helper import save_json
from src.helpers.chat_connector import ChatConnector


class ContentEnhancer:
    def __init__(self, logger, directory):
        self.logger = logger
        """Initialize the ContentEnhancer with source and output directories and JSON data paths."""
        self.source_dir = directory / 'blog_posts'
        self.output_dir = directory / 'enhanced_blog_posts'
        self.directory = directory
        self.filtered_urls = self._load_filtered_urls(directory / 'important.csv')

        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        self.model = ChatConnector(logger)
        self.model.init_model('gemini')
        # Load JSON data

        with open(directory / 'report' / 'linked.json', 'r', encoding='utf-8') as f:
            self.linked_data = json.load(f)

    def load_embeddings_from_json(self, input_file):
        """Load embeddings from a JSON file."""
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                self.embeddings = json.load(f)
            return True
        except Exception as e:
            self.logger.error(f'Error loading embeddings: {str(e)}')
            return False

    def _load_filtered_urls(self, csv_path):
        """Load list of important URLs from a CSV file."""
        important_urls = []
        try:
            if os.path.exists(csv_path):
                with open(csv_path, 'r', encoding='utf-8') as f:
                    csv_reader = csv.reader(f)
                    for row in csv_reader:
                        if row and len(row) > 0:
                            important_urls.append(row[0].strip())
                self.logger.info(f'Loaded {len(important_urls)} important URLs from {csv_path}')
            else:
                self.logger.warning(f'Important URLs file not found: {csv_path}')
        except Exception as e:
            self.logger.error(f'Error loading important URLs: {str(e)}')

        return important_urls

    def extract_frontmatter(self, content):
        """Extract YAML frontmatter from markdown content."""
        frontmatter_match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
        if frontmatter_match:
            frontmatter = frontmatter_match.group(1)
            content_without_frontmatter = content[frontmatter_match.end() :]
            return frontmatter, content_without_frontmatter
        return None, content

    def extract_title_and_content(self, content_without_frontmatter):
        """Extract title and main content from markdown."""
        lines = content_without_frontmatter.split('\n')
        title = lines[0].replace('#', '').strip() if lines else ''
        main_content = '\n'.join(lines[1:]).strip()
        return title, main_content

    def get_linked_articles(self, filename):
        """Get linked articles from the linked.json data."""
        if filename in self.linked_data:
            linked = self.linked_data[filename]['similar'].get('twins', [])
            return linked
        return []

    def get_linked_content(self, twins):
        """Retrieve content for linked articles."""
        linked_content = []
        for twin in twins:
            twin_filename = twin['document']
            with open(self.source_dir / twin_filename, 'r', encoding='utf-8') as f:
                content = f.read()
            frontmatter,_rest = self.extract_frontmatter(content)
            title, main = self.extract_title_and_content(_rest)

            linked_content.append(main)

        return linked_content

    async def enhance_content(self, original_content, filename):
        """Enhance the content with additional information and formatting."""
        self.logger.debug(f'Enhancing content for {filename}')
        result = {}

        frontmatter, content_without_frontmatter = self.extract_frontmatter(original_content)
        title, original_content = self.extract_title_and_content(content_without_frontmatter)
        result['frontmatter'] = frontmatter
        result['title'] = title
        result['original_content'] = original_content
        linked_articles = self.get_linked_articles(filename)
        result['linked_articles'] = linked_articles
        result['linked_content'] = self.get_linked_content(linked_articles)

        # Convert markdown to HTML for better text extraction
        html_content = markdown.markdown(original_content)
        soup = BeautifulSoup(html_content, 'html.parser')

        # Extract plain text for summary
        plain_text = soup.get_text()
        result['new_content'] = await self.generate_text_enhancement(original_content, result['linked_content'])

        # Create a summary (first 150 characters if content is long enough)
        result['summary'] = plain_text[:150] + '...' if len(plain_text) > 150 else plain_text
        result['key_points']=self._generate_key_points(plain_text)
        return result

    def build_enhanced_conted(self, content):
        enhanced_content = (
            '---\n'
            f'{content["frontmatter"]}\n'
            'enhanced: true\n'
            f'enhanced_date: {datetime.now().strftime("%Y-%m-%d")}\n'
            f'---\n'
            '\n'
            f'# {content["title"]}\n'
            '\n'
            '## Summary\n'
            f'{content["summary"]}\n'
            '## New Content\n'
            f'{content["new_content"]}\n'
            '\n'
            '## Original Content\n'
            f'{content["original_content"]}\n'
            '\n'
        )

        # Add linked articles section if available
        if content['linked_articles']:
            enhanced_content += '\n## Linked Resources\n'
            for i, link in enumerate(content['linked_articles']):
                enhanced_content += f'{i + 1}. [{link}]({link})\n'

        # Add additional sections
        enhanced_content += '\n## Key Takeaways\n'
        enhanced_content += '- ' + '\n- '.join(content['key_points'])

        return enhanced_content

    def _generate_key_points(self, text):
        """Generate key points from the text content."""
        # Simple approach: split text into sentences and pick first 3-5
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]

        # Return 3-5 key points or fewer if not enough content
        return sentences[: min(3, len(sentences))]

    def _get_source_url(self, content):
        """Extract source_url from frontmatter."""
        frontmatter, _ = self.extract_frontmatter(content)

        match = re.search(r'source_url:\s*(http[^\s\n]+)', frontmatter)
        if match:
            u= match.group(1).strip()
            u=u.split('#')[0]
            u=u.replace('http://','https://')
            return u
        
        return None

    async def generate_text_enhancement(self, origin, source_content: List[str]) -> str:
        """
        Generate a definition for a tag using LLM.

        Args:
            source_content: List of content from source files

        Returns:
            Generated definition for the tag
        """
        prompt = self._create_definition_prompt(origin, source_content)

        try:
            definition = await self.model.ask(prompt)
            return definition
        except Exception as e:
            return f'Definition generation failed: {e}'

    def _create_definition_prompt(self, origin, source_content: List[str]) -> str:
        """
        Create a prompt for the LLM to generate a tag definition.

        Args:
            source_content: List of content from source files

        Returns:
            Formatted prompt string
        """
        content_sample = '\n\n'.join(source_content[:5])  # Limit to first 3 sources to avoid token limits

        prompt = (
            'Based on the following articles that use the tag "{tag_name}", create a comprehensive definition\n'
            'of what this tag represents in the context of the Madar software system for Enterprise Resource Planning. \n'
            'It consist several modules like bookkeeping, payroll, warehouses, manufactory for polish small and medium companies.\n'
            ' Tag is polish word.\n'
            ' \n'
            '## Include:\n'
            '\n'
            '1. A concise 1-2 sentence definition\n'
            '2. The primary use cases or contexts where this tag applies\n'
            '3. Related features or modules in the software\n'
            '4. Any other important information about this tag\n'
            ''
            '## Origin content:\n'
            f'{origin}'
            '##  Related content:\n'
            f'{content_sample}'
            '\n'
            '## Rules\n'
            '1. Answer must be in polish language\n'
            '2. Please provide a well-structured definition that would help users understand what content\n'
            'they can expect to find under this tag.\n'
        )
        return prompt

    def save_enhanced_content(self, enhanced_content, filename):
        """Save enhanced content to a file."""
        # Create output filename
        output_filename = f'enhanced_{filename}'
        md=self.build_enhanced_conted(enhanced_content)
        output_path = os.path.join(self.output_dir, output_filename)

        # Save enhanced content
        self.logger.debug(f'Saving enhanced content to {output_path}')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(md)

        self.logger.info(f'Enhanced content saved to: {output_path}')
        return output_path

    async def process_files(self):
        """Process markdown files in the source directory whose source_url is in the important URLs list."""
        files_processed = 0
        files_skipped = 0

        # Get all markdown files
        md_files = glob.glob(os.path.join(self.source_dir, '*.md'))
        self.logger.info(f'Found {len(md_files)} markdown files to evaluate from {self.source_dir}')

        for file_path in md_files:
            filename = os.path.basename(file_path)

            try:
                # Read original content
                with open(file_path, 'r', encoding='utf-8') as f:
                    original_content = f.read()

                source_url = self._get_source_url(original_content)

                # Skip if source_url not in important_urls
                if not source_url or source_url not in self.filtered_urls:
                    # self.logger.debug(f"Skipping {filename} - source_url not in important URLs list")
                    files_skipped += 1
                    continue

                enhanced_content = await self.enhance_content(original_content, filename)
                save_json(enhanced_content,self.output_dir / f'{filename}_en.json')
                self.save_enhanced_content(enhanced_content, filename)
                files_processed += 1

            except Exception as e:
                self.logger.error(f'Error processing {filename}: {str(e)}')

        self.logger.info(
            f'\nProcessing complete! {files_processed} files were enhanced, {files_skipped} files were skipped.'
        )


if __name__ == '__main__':
    # Set up paths
    source_dir = r'c:\git\prompts\scraped\poznaj_madar\blog_posts'
