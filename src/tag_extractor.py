"""
Markdown Processor

Scans markdown files in a directory, extracts tags, and generates a summary report
"""

import os
import re
import yaml
import json
import logging
import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional


class TagExtractor:
    def __init__(self, logger):
        """
        Initialize the TagExtractor with a logger
        """
        self.logger = logger
        self.logger.info('TagExtractor initialized')

    def process_directory(self, directory):
        self.logger.debug(f'Processing directory: {directory}')
        files = self.get_markdown_files(directory)
        self.logger.info(f'Found {len(files)} markdown files')
        tag_map = self.extract_tags_from_files(files, directory)
        self.logger.info(f'Extracted {len(tag_map)} unique tags')
        return tag_map

    def get_markdown_files(self, directory: str) -> List[str]:
        try:
            files = [str(Path(directory) / f) for f in os.listdir(directory) if f.endswith('.md')]
            return files
        except Exception as e:
            self.logger.error(f'Error reading directory {directory}: {e}')
            return []

    def extract_frontmatter(self,content: str) -> Optional[Dict[str, Any]]:
        frontmatter_pattern = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)
        match = frontmatter_pattern.match(content)

        if match:
            try:
                return yaml.safe_load(match.group(1))
            except yaml.YAMLError as e:
                self.logger.error(f'Error parsing YAML frontmatter: {e}')

        return None



    def extract_tags_from_files(self, files: List[str], base_dir: str) -> Dict[str, List[Dict[str, str]]]:
        """
        Extract tags from markdown files

        Args:
            files: List of file paths
            base_dir: Base directory for relative paths in report

        Returns:
            Dictionary mapping tags to files containing them
        """
        tag_map = {}
        base_path = Path(base_dir)
        self.logger.info(f'Extracting tags from {len(files)} files')

        for file in files:
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    content = f.read()

                self.logger.debug(f'Processing file: {file}')
                data = self.extract_frontmatter(content)
                tags = data.get('tags', []) if data else []

                if not isinstance(tags, list):
                    tags = [tags]  # Convert single tag to list

                file_path = Path(file)
                relative_path = str(file_path.relative_to(base_path))
                title = data.get('title') if data else None

                if title is None:
                    title = file_path.stem

                for tag in tags:
                    if tag not in tag_map:
                        tag_map[tag] = []

                    tag_map[tag].append({'path': relative_path, 'title': title})

            except Exception as e:
                self.logger.error(f'Error processing file {file}: {e}')

        self.logger.info(f'Processed {len(files)} files, found {len(tag_map)} unique tags')
        return tag_map

    def generate_yaml_report(self, tag_map: Dict[str, List[Dict[str, str]]]) -> str:
        """
        Generate markdown report from tag map

        Args:
            tag_map: Dictionary mapping tags to files

        Returns:
            Markdown formatted report
        """
        report = '# Tag Summary Report\n\n'

        # Add generation timestamp
        report += f'*Generated on: {datetime.datetime.now().isoformat()}*\n\n'

        # Add tag summary
        tags = sorted(tag_map.keys())
        report += f'## All Tags ({len(tags)})\n\n'

        for tag in tags:
            # Create anchor link by converting tag to lowercase and replacing spaces with hyphens
            anchor = tag.lower().replace(' ', '-')
            report += f'- [{tag}](#{anchor}) ({len(tag_map[tag])} sources)\n'

        # Add detailed sections for each tag
        report += '\n## Tag Details\n\n'

        for tag in tags:
            report += f'### {tag}\n\n'
            report += f'Sources containing this tag: {len(tag_map[tag])}\n\n'

            for file in tag_map[tag]:
                report += f'- [{file["title"]}]({file["path"]})\n'

            report += '\n'

        self.logger.info('YAML report generation completed')
        return report

    def generate_json_report(self, tag_map: Dict[str, List[Dict[str, str]]]) -> str:
        """
        Generate JSON report from tag map

        Args:
            tag_map: Dictionary mapping tags to files

        Returns:
            JSON formatted report as string
        """
        self.logger.info('Generating JSON report')
        report = {
            'meta': {
                'title': 'Tag Summary Report',
                'description': 'Summary of tags and their occurrences in markdown files',
                'generated_at': datetime.datetime.now().isoformat(),
                'total_tags': len(tag_map),
            },
            'tag_details': {},
        }

        # Create summary info for each tag
        for tag, files in tag_map.items():
            # Add detailed info for each file containing the tag
            report['tag_details'][tag] = {'count': len(files), 'sources': files}

        self.logger.info('JSON report generation completed')
        return json.dumps(report, indent=2)



    # Example usage
    # extractor = TagExtractor()
    # input_directory = os.path.join("c:\\git\\prompts", "scraped", "invoicer_blogspot")

    # Markdown report
    # md_report = extractor.process_directory(input_directory)
    # with open('./tag-report.md', 'w', encoding='utf-8') as f:
    #     f.write(md_report)

    # JSON report
    # json_report = extractor.generate_json_report(md_report)
    # with open('./tag-report.json', 'w', encoding='utf-8') as f:
    #     f.write(json_report)
