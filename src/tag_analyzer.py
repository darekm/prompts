import json
import os
import logging
from typing import Dict, List, Any
from pathlib import Path

from src.helpers.chat_connector import ChatConnector


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
        self.output_dir = base_dir / 'report'
        self.data_dir = base_dir / 'blog_posts'
        self.tag_data = None
        self.model = ChatConnector(logger)
        self.model.init_model('gemini')

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

    def generate_tag_definition(self, tag_name: str, source_content: List[str]) -> str:
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
            definition = self.model.ask_sync(prompt)
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

    def process_tags(self, tags) -> Dict[str, str]:
        """
        Process all tags and generate definitions.

        Returns:
            Dictionary mapping tag names to their definitions
        """

        tag_definitions = {}

        for tag_name in tags:
            self.logger.info(f'Processing tag: {tag_name}')
            tag_definitions[tag_name] = self.process_tag(tag_name)
        

        return tag_definitions

    def process_tag(self, tag_name: str) :
        sources = self.get_tag_sources(tag_name)

        # Extract content from the source files
        source_content = []
        for source in sources:
            if 'path' in source:
                content = self.read_source_content(source['path'])
                if content:
                    source_content.append(content)

        # Generate definition
        if source_content:
            text= self.generate_tag_definition(tag_name, source_content)
        else:
            self.logger.warning(f"No content found for tag '{tag_name}'")
            text=''
        return {
            'tag_name': tag_name,
            'definition': text,
            'sources': sources
        }
    def save_tags(self, tag_definitions):
        for tag in tag_definitions.keys():
            self.logger.info(f'Processing tag: {tag}')
            output_file = os.path.join(self.output_dir,  f'{tag}.md')
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f'# {tag}\n\n')
                f.write(f'## Definition\n{tag_definitions[tag]['definition']}\n\n')
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
