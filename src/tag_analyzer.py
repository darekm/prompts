import json
import os
import logging
import numpy as np
from typing import Dict, List, Any, Tuple
from pathlib import Path

from src.helpers.chat_connector import ChatConnector
from src.helpers.embedding_connector import EmbeddingConnector
from src.helpers.np_helper import cosine_similarity


class TagAnalyzer:
    """Class for analyzing tags from blog post data and generating definitions."""

    def __init__(self, logger: logging.Logger, json_file_path: Path, base_dir: Path):
        """
        Initialize the TagAnalyzer.

        Args:
            logger: Logger for logging information
            json_file_path: Path to the JSON file containing tag data
            output_dir: Directory to save the output files
            api_key: API key for the LLM service (optional)
        """
        self.logger = logger
        self.json_file_path = json_file_path
        self.md_dir = base_dir / 'md'
        self.output_dir = base_dir / 'report'
        self.data_dir = base_dir / 'blog_posts'
        self.tag_data = None
        self.model = ChatConnector(logger)
        self.model.init_model('gemini')
        self.embedding_model = EmbeddingConnector(logger)
        self.embedding_model.init_model('google')
        self.embedding_data = None
        self.embeddings_file = base_dir / 'embedding.json'

    def load_json_data(self) -> Dict[str, Any]:
        """
        Load the JSON data from the file.

        Returns:
            The loaded JSON data
        """
        try:
            with open(self.json_file_path, 'r', encoding='utf-8') as f:
                self.tag_data = json.load(f)
            return self.tag_data
        except Exception as e:
            self.logger.error(f'Error loading JSON data: {e}')
            raise

    def load_embeddings(self) -> Dict[str, Any]:
        """
        Load embeddings from the embedding.json file.

        Returns:
            Dictionary of post embeddings
        """
        try:
            if not os.path.exists(self.embeddings_file):
                self.logger.warning(f"Embeddings file {self.embeddings_file} not found")
                return {}

            with open(self.embeddings_file, 'r', encoding='utf-8') as f:
                self.embedding_data = json.load(f)

            self.logger.info(f"Loaded embeddings for {len(self.embedding_data)} posts")
            return self.embedding_data
        except Exception as e:
            self.logger.error(f"Error loading embeddings data: {e}")
            return {}

    def get_unique_tags(self) -> List[str]:
        """
        Extract unique tags from the JSON data.

        Returns:
            List of unique tag names
        """
        if not self.tag_data:
            self.load_json_data()

        tags = []
        if 'tag_details' in self.tag_data:
            tags = list(self.tag_data['tag_details'].keys())
            self.logger.info(f'Found {len(tags)} unique tags')
        else:
            self.logger.warning('No tag_details found in the JSON data')

        return tags

    def get_tag_sources(self, tag_name: str) -> List[Dict[str, str]]:
        """
        Get the sources for a specific tag.

        Args:
            tag_name: The name of the tag

        Returns:
            List of source dictionaries containing path and title
        """
        if not self.tag_data:
            self.load_json_data()

        sources = []
        if 'tag_details' in self.tag_data and tag_name in self.tag_data['tag_details']:
            sources = self.tag_data['tag_details'][tag_name].get('sources', [])

        return sources

    async def generate_tag_definition(self, tag_name: str, source_content: List[str]) -> str:
        """
        Generate a definition for a tag using LLM.

        Args:
            tag_name: The name of the tag
            source_content: List of content from source files

        Returns:
            Generated definition for the tag
        """
        prompt = self._create_definition_prompt(tag_name, source_content)

        try:
            definition = await self.model.ask(prompt)
            return definition
        except Exception as e:
            self.logger.error(f"Error generating definition for tag '{tag_name}': {e}")
            return f'Definition generation failed: {e}'

    def _create_definition_prompt(self, tag_name: str, source_content: List[str]) -> str:
        """
        Create a prompt for the LLM to generate a tag definition.

        Args:
            tag_name: The name of the tag
            source_content: List of content from source files

        Returns:
            Formatted prompt string
        """
        content_sample = '\n\n'.join(source_content[:3])  # Limit to first 3 sources to avoid token limits

        prompt = f"""
Based on the following articles that use the tag '{tag_name}', create a comprehensive definition
of what this tag represents in the context of the Madar software system for Enterprise Resource Planning. 
It consist several modules like bookkeeping, payroll, warehouses, manufactory for polish small and medium companies.
 Tag is polish word. 

## Include:

1. A concise 1-2 sentence definition
2. The primary use cases or contexts where this tag applies
3. Related features or modules in the software
4. Any other important information about this tag

##  Source content samples:
{content_sample}

## Rukes
1. Answer must be in polish language
2. Please provide a well-structured definition that would help users understand what content
they can expect to find under this tag.
"""
        return prompt

    def read_source_content(self, source_name: str) -> str:
        """
        Read content from a source markdown file.

        Args:
            source_path: Path to the source file

        Returns:
            The content of the file as a string
        """
        full_path = os.path.join(self.data_dir, source_name)
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            self.logger.warning(f'Could not read file {full_path}: {e}')
            return ''

    def url_frendly(self, tag_name: str) -> str:
        """
        Convert a tag name to a URL-friendly format.

        Args:
            tag_name: The name of the tag

        Returns:
            URL-friendly string
        """
        import re
        # Convert to lowercase
        result = tag_name.lower()
        # Replace polish characters
        polish_chars = {
            'ą': 'a', 'ć': 'c', 'ę': 'e', 'ł': 'l', 'ń': 'n',
            'ó': 'o', 'ś': 's', 'ź': 'z', 'ż': 'z'
        }
        for pol, eng in polish_chars.items():
            result = result.replace(pol, eng)
        # Replace spaces with hyphens
        result = result.replace(' ', '-')
        # Remove any non-alphanumeric characters (except hyphens)
        result = re.sub(r'[^a-z0-9-]', '', result)
        # Replace multiple hyphens with single hyphen
        result = re.sub(r'-+', '-', result)
        # Remove leading and trailing hyphens
        result = result.strip('-')

        return result

    def generate_contents(self, tags: List[str]) -> str:
        """
        Generate a table of contents (spis tresci) in markdown format for the given tags.

        Args:
            tags: List of tag names

        Returns:
            A markdown string representing the table of contents
        """

        contents = '# Spis Treści\n\n'
        for tag in tags:
            contents += f'- [{tag}](./{self.url_frendly(tag)}.html)\n'
        output_file = os.path.join(self.md_dir, 'content.md')
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(contents)

        return contents

    def find_similar_posts(self, embedding: List[float], n: int = 5) -> List[Dict[str, Any]]:
        """
        Find the n most similar posts to the given embedding using cosine similarity.

        Args:
            embedding: The embedding vector to compare against
            n: Number of similar posts to return

        Returns:
            List of the n most similar posts with similarity scores
        """
        if not self.embedding_data:
            self.load_embeddings()

        if not self.embedding_data or not embedding:
            return []

        similarities = []

        # Convert the tag embedding to a numpy array
        tag_embedding = np.array(embedding)

        # Calculate cosine similarity for each post embedding
        for post_id, post_data in self.embedding_data.items():
            if 'embedding' not in post_data or not post_data['embedding']:
                continue

            post_embedding = np.array(post_data['embedding'])

            # Calculate cosine similarity using the imported function
            similarity = cosine_similarity(tag_embedding, post_embedding)

            post_info = {
                'id': post_id,
                'title': post_data.get('title', 'Unknown'),
                'path': post_data.get('path', ''),
                'similarity': float(similarity)
            }

            similarities.append(post_info)

        # Sort by similarity (descending)
        sorted_similarities = sorted(similarities, key=lambda x: x['similarity'], reverse=True)

        # Return the top n results
        return sorted_similarities[:n]

    async def process_tags(self, tags) -> Dict[str, str]:
        """
        Process all tags and generate definitions.

        Returns:
            Dictionary mapping tag names to their definitions
        """

        tag_definitions = {}

        for tag_name in tags:
            self.logger.info(f'Processing tag: {tag_name}')
            tag_definitions[tag_name] = await self.process_tag(tag_name)

        return tag_definitions

    async def process_tag(self, tag_name: str):
        sources = self.get_tag_sources(tag_name)

        # Extract content from the source files
        source_content = []
        for source in sources:
            if 'path' in source:
                content = self.read_source_content(source['path'])
                if content:
                    source_content.append(content)

        # Generate definition
        text = ''
        embedding = None
        similar_posts = []

        if source_content:
            text = await self.generate_tag_definition(tag_name, source_content)

            # Compute embedding for the definition
            if text:
                try:
                    self.logger.info(f"Computing embedding for tag '{tag_name}'")
                    embedding = await self.embedding_model.embed(text)

                    # Find similar posts
                    if embedding:
                        self.logger.info(f"Finding similar posts for tag '{tag_name}'")
                        similar_posts = self.find_similar_posts(embedding)
                        self.logger.info(f"Found {len(similar_posts)} similar posts for tag '{tag_name}'")

                except Exception as e:
                    self.logger.error(f"Error computing embedding for tag '{tag_name}': {e}")
                    embedding = None
        else:
            self.logger.warning(f"No content found for tag '{tag_name}'")

        return {
            'tag_name': tag_name,
            'definition': text,
            'sources': sources,
            'embedding': embedding,
            'similar_posts': similar_posts
        }

    def save_tags(self, tag_definitions):
        for tag in tag_definitions.keys():
            self.logger.info(f'Processing tag: {tag}')
            output_file = os.path.join(self.md_dir, f'{self.url_frendly(tag)}.md')
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f'# {tag}\n\n')
                f.write(f'## Definition\n{tag_definitions[tag]["definition"]}\n\n')

                # Add similar posts section if available
                if 'similar_posts' in tag_definitions[tag] and tag_definitions[tag]['similar_posts']:
                    f.write('## Similar Posts\n')
                    for post in tag_definitions[tag]['similar_posts']:
                        similarity_percentage = round(post['similarity'] * 100, 2)
                        f.write(f"- [{post['title']}]({post['path']}) - {similarity_percentage}% similar\n")
                    f.write('\n')

                f.write('## Sources\n')
                for source in tag_definitions[tag]['sources']:
                    f.write(f'- {source["title"]}: [{source["path"]}]\n')

    def save_tags_to_json(self, tag_definitions: Dict[str, str]) -> str:
        """
        Save the tag definitions to a file.

        Args:
            tag_definitions: Dictionary of tag names and their definitions

        Returns:
            Path to the saved file
        """
        output_file = os.path.join(self.output_dir, 'report', 'tag-definitions.json')
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        output_data = {
            'meta': {
                'title': 'Tag Definitions',
                'description': 'Definitions for tags used in the blog posts',
                'total_tags': len(tag_definitions),
            },
            'definitions': tag_definitions,
        }

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)

            self.logger.info(f'Tag definitions processed {len(tag_definitions)}  saved to {output_file}')

            return output_file
        except Exception as e:
            self.logger.error(f'Error saving tag definitions: {e}')
            raise
