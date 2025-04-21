import json
import os
import logging
import numpy as np
from typing import Dict, List, Any
from pathlib import Path

from src.helpers.string_helper import url_frendly
from src.helpers.chat_connector import ChatConnector
from src.helpers.embedding_connector import EmbeddingConnector
from src.helpers.np_helper import cosine_similarity


class TagAnalyzer:
    """Class for analyzing tags from blog post data and generating definitions."""

    def __init__(self, logger: logging.Logger, base_dir: Path):
        """
        Initialize the TagAnalyzer.

        Args:
            logger: Logger for logging information
            base_dir: Base directory for the blog posts and reports
        """
        self.logger = logger
        self.md_dir = base_dir / 'md'
        self.output_dir = base_dir / 'report'
        self.data_dir = base_dir / 'blog_posts'
        self.tag_data = None
        self.model = ChatConnector(logger)
        self.model.init_model('gemini')
        self.embedding_model = EmbeddingConnector(logger)
        self.embedding_model.init_model('google')
        self.embeddings = None

    def load_tag_report(self) -> Dict[str, Any]:
        if not self.embeddings:
            self.load_embeddings()

        file_path = self.output_dir / 'tag-report.json'
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.tag_data = json.load(f)
            return self.tag_data
        except Exception as e:
            self.logger.error(f'Error loading JSON data: {e}')
            raise

    def load_embeddings(self):
        try:
            with open(self.output_dir / 'embeddings.json', 'r', encoding='utf-8') as f:
                self.embeddings = json.load(f)

            self.logger.info(f'Loaded embeddings for {len(self.embeddings)} posts')
            return True
        except Exception as e:
            self.logger.error(f'Error loading embeddings data: {e}')
            return False

    def get_unique_tags(self) -> List[str]:
        """
        Extract unique tags from the JSON data.

        Returns:
            List of unique tag names
        """

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
            self.load_tag_report()

        sources = []
        if 'tag_details' in self.tag_data and tag_name in self.tag_data['tag_details']:
            sources = self.tag_data['tag_details'][tag_name].get('sources', [])
        for file in sources:
            file['source_url'] = self.embeddings[file['path']].get('source_url', '')
        return sources

    def _create_definition_prompt(self, tag_name: str, source_content: List[str]) -> str:
        """
        Create a prompt for the LLM to generate a tag definition.

        Args:
            tag_name: The name of the tag
            source_content: List of content from source files

        Returns:
            Formatted prompt string
        """
        content_sample = '\n\n'.join(source_content[:5])  # Limit to first 3 sources to avoid token limits

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
            contents += f'- [{tag}](./{url_frendly(tag)}.html)\n'
        output_file = os.path.join(self.md_dir, 'content.md')
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(contents)

        return contents

    def find_similar_posts(self, embedding, n: int = 5) -> List[Dict[str, Any]]:
        """
        Find the n most similar posts to the given embedding using cosine similarity.

        Args:
            embedding: The embedding vector to compare against
            n: Number of similar posts to return

        Returns:
            List of the n most similar posts with similarity scores
        """

        if not self.embeddings or not embedding:
            return []

        similarities = []

        tag_embedding = np.array(embedding)

        # Calculate cosine similarity for each post embedding
        for post_id, post_data in self.embeddings.items():
            if 'embedding' not in post_data or not post_data['embedding']:
                continue

            post_embedding = np.array(post_data['embedding'])
            similarity = cosine_similarity(tag_embedding, post_embedding)

            post_info = {
                'id': post_id,
                #'title': post_data.get('title', 'Unknown'),
                'source_url': post_data.get('source_url', ''),
                'tags': post_data.get('tags', []),
                'path': post_id,
                'similarity': float(similarity),
            }

            similarities.append(post_info)

        sorted_similarities = sorted(similarities, key=lambda x: x['similarity'], reverse=True)
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
            self.store_tag(tag_definitions[tag_name])

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
        definition = ''
        definition_embedding = None
        similar_posts = []

        if source_content:
            prompt = self._create_definition_prompt(tag_name, source_content)       
            definition = await self.model.ask(prompt)
            # Compute embedding for the definition
            if definition:
                try:
                    self.logger.info(f"Computing embedding for tag '{tag_name}'")
                    definition_embedding = await self.embedding_model.embed(definition)

                    similar_posts = self.find_similar_posts(definition_embedding)
                    self.logger.info(f"Found {len(similar_posts)} similar posts for tag '{tag_name}'")

                except Exception as e:
                    self.logger.error(f"Error computing embedding for tag '{tag_name}': {e}")
                    definition_embedding = None
        else:
            self.logger.warning(f"No content found for tag '{tag_name}'")

        return {
            'tag_name': tag_name,
            'definition': definition,
            'sources': sources,
            'embedding': definition_embedding,
            'similar_posts': similar_posts,
        }

    def save_tags(self, tag_definitions):
        for tag in tag_definitions.keys():
            self.store_tag(tag_definitions[tag])

    def _check_sources(self, source, links) -> bool:
        for link in links:
            if source == link['path']:
                return True
        return False

    def store_tag(self, definition: Dict[str, str]):
        tag = definition['tag_name']
        self.logger.info(f'Saving tag: {tag}')
        output_file = os.path.join(self.md_dir, f'{url_frendly(tag)}.md')
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f'# {tag}\n\n')
            f.write(f'## Definition\n{definition["definition"]}\n\n')

            # Add similar posts section if available
            if 'similar_posts' in definition and definition['similar_posts'] and (len(definition['sources']) < 8):
                f.write('## Similar Posts\n')
                for post in definition['similar_posts']:
                    if post['similarity'] < 0.83:
                        continue
                    if 'sources' in definition and 'id' in post:
                        if self._check_sources(post['id'], definition['sources']):
                            continue

                    similarity_percentage = round(post['similarity'] * 100, 2)
                    f.write(f'- ({post["id"]}) - {similarity_percentage}% [similar]( {post["source_url"]})\n  ')
                f.write('\n')

            f.write('## Sources\n')
            for source in definition['sources']:
                f.write(f'- [{source["title"]}]({source["source_url"]})\n')

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
