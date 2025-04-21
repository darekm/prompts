import os
import argparse
import yaml

from src.helpers.string_helper import clean_url
from src.helpers.chat_connector import ChatConnector
from src.helpers.embedding_connector import EmbeddingConnector
from src.helpers.np_helper import  save_json


class MarkdownEmbeddingGenerator:
    """Class to generate embeddings for markdown files in a directory."""

    def __init__(self, logger):
        # Set up logger
        self.logger = logger
        model_type = 'google'
        model_chat = 'gemini'
        self.embeddings = {}

        # Initialize the embedding connector
        self.logger.info(f'Initializing {model_type} embedding model')
        self.connector = EmbeddingConnector(self.logger)
        self.connector.init_model(model_type)
        self.chat = ChatConnector(self.logger)
        self.chat.init_model(model_chat)

    def extract_markdown_body(self, content: str) -> str:
        """Extract the body content from a markdown file, excluding frontmatter."""

        # Check if the file has YAML frontmatter (between --- markers)
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                # Return everything after the frontmatter
                return parts[2].strip()

        # If no frontmatter is detected, return the entire content
        return content.strip()

    def extract_yaml(self, content: str) -> dict:
        """Extract the YAML frontmatter from the markdown file."""
        yaml_content = {}

        # Check if the file has YAML frontmatter (between --- markers)
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                try:
                    # Parse the YAML frontmatter
                    yaml_content = yaml.safe_load(parts[1])
                except Exception as e:
                    self.logger.error(f'Error parsing frontmatter YAML: {str(e)}')

        return yaml_content

    def extract_frontmatter_field(self, content: str, field_name: str, default=None):
        """Extract a specific field from frontmatter YAML.

        Args:
            content: The full content of the markdown file
            field_name: Name of the field to extract
            default: Default value to return if field is not found

        Returns:
            Value of the requested field, or default value if not found
        """
        frontmatter = self.extract_yaml(content)
        if frontmatter and field_name in frontmatter:
            return frontmatter[field_name]
        return default

    def extract_links(self, content: str) -> list:
        return self.extract_frontmatter_field(content, 'related_links', [])

    def extract_tags(self, content: str) -> list:
        return self.extract_frontmatter_field(content, 'tags', [])

    def extract_source_url(self, content: str) -> str:
        return self.extract_frontmatter_field(content, 'source_url', '')

    async def summarize(self, content: str) -> str:
        """Summarize the content using the chat model."""
        self.logger.debug('Summarizing content')
        prompt = (
            'Your task is helping me to create better manual to program Madar.\n'
            'Given the content below, please summarize it in a concise and clear manner.\n'
            'Make sure to include all important information.\n'
            'Rules:\n'
            '1. Do not include any code snippets.\n'
            '2. Do not include any links.\n'
            '3. Do not include any tags.\n'
            '4. Do not include any frontmatter.\n'
            '5. Summary must be in Polish.\n'
            '6. Do not include any explanations.\n'
            '7. Length of the summary should be near 30 words.\n'
            'Please summarize the following content:\n\n'
            f'{content}'
        )
        response = await self.chat.ask(prompt)
        return response

    def process_links(self, directory_path):
        file_count = 0

        self.logger.debug(f'Traversing directory: {directory_path}')
        embeddings_data = {}

        # Walk through the directory
        for root, _, files in os.walk(directory_path):
            for file in files:
                if file.endswith('.md'):
                    file_path = os.path.join(root, file)
                    try:
                        self.logger.debug(f'Processing: {file_path}')

                        # Extract body content
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()

                        # body_content = self.extract_markdown_body(content)
                        related_links = self.extract_links(content)
                        for links in related_links:
                            links['url'] = clean_url(links['url'])

                        tags = self.extract_tags(content)
                        source = clean_url(self.extract_source_url(content))
                        # Store relative path and embedding
                        rel_path = os.path.relpath(file_path, directory_path)
                        embeddings_data[rel_path] = {
                            'id': rel_path,
                            'related_links': related_links,
                            'tags': tags,
                            'source_url': source,
                        }

                        file_count += 1
                    except Exception as e:
                        self.logger.error(f'Error processing {file_path}: {str(e)}')
                        break
        self.embeddings = embeddings_data
        self.repair_path()
        return file_count

    async def process_directory(self, directory_path):
        """
        Process all markdown files in the given directory, compute embeddings,
        and store them in a JSON file.

        Args:
            directory_path: Path to directory containing markdown files
        """
        file_count = 0

        self.logger.debug(f'Traversing directory: {directory_path}')
        embeddings_data = {}

        # Walk through the directory
        for root, _, files in os.walk(directory_path):
            for file in files:
                if file.endswith('.md'):
                    file_path = os.path.join(root, file)
                    try:
                        self.logger.debug(f'Processing: {file_path}')

                        # Extract body content
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()

                        body_content = self.extract_markdown_body(content)
                        related_links = self.extract_links(content)
                        tags = self.extract_tags(content)
                        source = clean_url(self.extract_source_url(content))
                        embedding = await self.connector.embed(body_content)
                        # summary = await self.summarize(body_content)

                        # Store relative path and embedding
                        rel_path = os.path.relpath(file_path, directory_path)
                        embeddings_data[rel_path] = {
                            'id': rel_path,
                            'embedding': embedding,
                            'related_links': related_links,
                            'tags': tags,
                            #'summary': summary,
                            'source_url': source,
                        }

                        file_count += 1
                    except Exception as e:
                        self.logger.error(f'Error processing {file_path}: {str(e)}')
                        break
        self.embeddings = embeddings_data
        self.repair_path()
        return file_count

    def repair_path(self):
        for file_name in self.embeddings.keys():
            file1 = self.embeddings[file_name]
            file1['id'] = file_name
            file1['source_url'] = clean_url(file1['source_url'])
            for file2 in self.embeddings.values():
                for links in file2['related_links']:
                    if file1['source_url'] == links['url']:
                        links['path'] = file_name
                        print(file_name)

    def save_embeddings_to_json(self, output_file):
        save_json(self.embeddings, output_file)
        self.logger.info(f'Saving {len(self.embeddings)} embeddings to {output_file}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate embeddings and cluster markdown files')
    parser.add_argument('--directory', '-d', type=str, help='Directory containing markdown files')
    parser.add_argument('--output', '-o', type=str, help='Output JSON file path for embeddings')
    parser.add_argument(
        '--model',
        '-m',
        type=str,
        default='gemini',
        choices=['gemini', 'openai', 'azure'],
        help='Embedding model type to use (gemini, openai, or azure)',
    )
    parser.add_argument('--input', '-i', type=str, help='Input JSON file containing pre-computed embeddings')
    parser.add_argument('--cluster', '-c', action='store_true', help='Perform clustering on the embeddings')

    args = parser.parse_args()

    # Configure logging
    import logging

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger('md_embeddings')

    # Create instance of the embedding generator
    generator = MarkdownEmbeddingGenerator(logger)
