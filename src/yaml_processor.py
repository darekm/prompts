"""
Markdown Processor

Scans markdown files in a directory, extracts tags, and generates a summary report
"""

import os
import re
import yaml
import json
import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional


class YamlProcessor:
    @staticmethod
    def process_directory(directory: str) -> str:
        """
        Process markdown files in a directory and generate a tag dictionary

        Args:
            directory: Directory path containing markdown files

        """
        files = YamlProcessor.get_markdown_files(directory)
        tag_map = YamlProcessor.extract_tags_from_files(files, directory)
        return tag_map

    @staticmethod
    def get_markdown_files(directory: str) -> List[str]:
        """
        Get all markdown files in a directory

        Args:
            directory: Directory to scan

        Returns:
            List of file paths
        """
        try:
            return [str(Path(directory) / f) for f in os.listdir(directory) if f.endswith('.md')]
        except Exception as e:
            print(f'Error reading directory {directory}: {e}')
            return []

    @staticmethod
    def extract_frontmatter(content: str) -> Optional[Dict[str, Any]]:
        """
        Extract YAML frontmatter from markdown content

        Args:
            content: Markdown content

        Returns:
            Dictionary containing frontmatter data or None
        """
        frontmatter_pattern = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)
        match = frontmatter_pattern.match(content)

        if match:
            try:
                return yaml.safe_load(match.group(1))
            except yaml.YAMLError as e:
                print(f'Error parsing YAML frontmatter: {e}')

        return None

    @staticmethod
    def extract_tags_from_files(files: List[str], base_dir: str) -> Dict[str, List[Dict[str, str]]]:
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

        for file in files:
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    content = f.read()

                data = YamlProcessor.extract_frontmatter(content)
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
                print(f'Error processing file {file}: {e}')

        return tag_map

    @staticmethod
    def generate_yaml_report(tag_map: Dict[str, List[Dict[str, str]]]) -> str:
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

        return report

    @staticmethod
    def generate_json_report(tag_map: Dict[str, List[Dict[str, str]]]) -> str:
        """
        Generate JSON report from tag map

        Args:
            tag_map: Dictionary mapping tags to files

        Returns:
            JSON formatted report as string
        """
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

        # Convert to formatted JSON string
        return json.dumps(report, indent=2)


if __name__ == '__main__':
    pass
    # Example usage
    # input_directory = os.path.join("c:\\git\\prompts", "scraped", "invoicer_blogspot")

    # Markdown report
    # md_report = YamlProcessor.process_directory(input_directory)
    # with open('./tag-report.md', 'w', encoding='utf-8') as f:
    #     f.write(md_report)

    # JSON report
    # json_report = YamlProcessor.process_directory_json(input_directory)
    # with open('./tag-report.json', 'w', encoding='utf-8') as f:
    #     f.write(json_report)
