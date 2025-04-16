import os
import json
import re
import markdown
from bs4 import BeautifulSoup
import glob
import csv
from datetime import datetime

class ContentEnhancer:
    def __init__(self, logger,directory):
        self.logger=logger
        """Initialize the ContentEnhancer with source and output directories and JSON data paths."""
        self.source_dir = directory / 'blog_posts'
        self.output_dir = directory / 'enhanced_blog_posts'
        self.directory = directory
        self.important_urls = self._load_important_urls(directory / 'important.csv')
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Load JSON data
        with open(directory / 'report' / 'similar.json', 'r', encoding='utf-8') as f:
            self.similar_data = json.load(f)
        
        with open(directory / 'report' / 'linked.json', 'r', encoding='utf-8') as f:
            self.linked_data = json.load(f)
    
    def _load_important_urls(self, csv_path):
        """Load list of important URLs from a CSV file."""
        important_urls = []
        try:
            if os.path.exists(csv_path):
                with open(csv_path, 'r', encoding='utf-8') as f:
                    csv_reader = csv.reader(f)
                    for row in csv_reader:
                        if row and len(row) > 0:
                            important_urls.append(row[0].strip())
                self.logger.info(f"Loaded {len(important_urls)} important URLs from {csv_path}")
            else:
                self.logger.warning(f"Important URLs file not found: {csv_path}")
        except Exception as e:
            self.logger.error(f"Error loading important URLs: {str(e)}")
        
        return important_urls
    
    def extract_frontmatter(self, content):
        """Extract YAML frontmatter from markdown content."""
        frontmatter_match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
        if frontmatter_match:
            frontmatter = frontmatter_match.group(1)
            content_without_frontmatter = content[frontmatter_match.end():]
            return frontmatter, content_without_frontmatter
        return None, content
    
    def extract_title_and_content(self, content_without_frontmatter):
        """Extract title and main content from markdown."""
        lines = content_without_frontmatter.split('\n')
        title = lines[0].replace('#', '').strip() if lines else ""
        main_content = '\n'.join(lines[1:]).strip()
        return title, main_content
    
    def get_similar_articles(self, filename):
        """Get similar articles from the similar.json data."""
        if filename in self.similar_data:
            twins = self.similar_data[filename].get('twins', [])
            result = []
            
            # Extract up to 3 similar articles with sources
            for i, twin in enumerate(twins):
                if i >= 3:  # Limit to 3 similar articles
                    break
                    
                if isinstance(twin, list) and len(twin) > 0:
                    result.append(twin[0])  # First element is the filename
                elif isinstance(twin, dict) and 'source' in twin:
                    result.append(twin['source'])
            
            return result
        return []
    
    def get_linked_articles(self, filename):
        """Get linked articles from the linked.json data."""
        if filename in self.linked_data:
            linked = self.linked_data[filename].get('linked', [])
            return linked
        return []
    
    def enhance_content(self, original_content, filename):
        """Enhance the content with additional information and formatting."""
        self.logger.debug(f"Enhancing content for {filename}")
            
        frontmatter, content_without_frontmatter = self.extract_frontmatter(original_content)
        title, main_content = self.extract_title_and_content(content_without_frontmatter)
        
        # Get similar and linked articles
        similar_articles = self.get_similar_articles(filename)
        linked_articles = self.get_linked_articles(filename)
        
        # Convert markdown to HTML for better text extraction
        html_content = markdown.markdown(main_content)
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract plain text for summary
        plain_text = soup.get_text()
        
        # Create a summary (first 150 characters if content is long enough)
        summary = plain_text[:150] + "..." if len(plain_text) > 150 else plain_text
        
        # Build enhanced content
        enhanced_content = f"""---
{frontmatter}
enhanced: true
enhanced_date: {datetime.now().strftime('%Y-%m-%d')}
---

# {title}

## Summary
{summary}

## Original Content
{main_content}

"""
        
        # Add similar articles section if available
        if similar_articles:
            enhanced_content += "\n## Related Articles\n"
            for i, article in enumerate(similar_articles):
                enhanced_content += f"{i+1}. [{article}]({article})\n"
        
        # Add linked articles section if available
        if linked_articles:
            enhanced_content += "\n## Linked Resources\n"
            for i, link in enumerate(linked_articles):
                enhanced_content += f"{i+1}. [{link}]({link})\n"
        
        # Add additional sections
        enhanced_content += "\n## Key Takeaways\n"
        enhanced_content += "- " + "\n- ".join(self._generate_key_points(plain_text))
        
        return enhanced_content
    
    def _generate_key_points(self, text):
        """Generate key points from the text content."""
        # Simple approach: split text into sentences and pick first 3-5
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        
        # Return 3-5 key points or fewer if not enough content
        return sentences[:min(3, len(sentences))]
    
    def _get_source_url(self, content):
        """Extract source_url from frontmatter."""
        frontmatter, _ = self.extract_frontmatter(content)
           
        match = re.search(r'source_url:\s*(http[^\s\n]+)', frontmatter)
        if match:
            return match.group(1).strip()
        return None
    
    def save_enhanced_content(self, enhanced_content, filename):
        """Save enhanced content to a file."""
        # Create output filename
        output_filename = f"enhanced_{filename}"
        output_path = os.path.join(self.output_dir, output_filename)
        
        # Save enhanced content
        self.logger.debug(f"Saving enhanced content to {output_path}")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(enhanced_content)
        
        self.logger.info(f"Enhanced content saved to: {output_path}")
        return output_path
    
    def process_files(self):
        """Process markdown files in the source directory whose source_url is in the important URLs list."""
        files_processed = 0
        files_skipped = 0
        
        # Get all markdown files
        md_files = glob.glob(os.path.join(self.source_dir, "*.md"))
        self.logger.info(f"Found {len(md_files)} markdown files to evaluate from {self.source_dir}")
        
        for file_path in md_files:
            filename = os.path.basename(file_path)
            
            try:
                # Read original content
                with open(file_path, 'r', encoding='utf-8') as f:
                    original_content = f.read()
                
                
                source_url = self._get_source_url(original_content)
                
                # Skip if source_url not in important_urls
                if not source_url or source_url not in self.important_urls:
                    # self.logger.debug(f"Skipping {filename} - source_url not in important URLs list")
                    files_skipped += 1
                    continue
                
                enhanced_content = self.enhance_content(original_content, filename)
                self.save_enhanced_content(enhanced_content, filename)
                files_processed += 1
                
            except Exception as e:
                self.logger.error(f"Error processing {filename}: {str(e)}")
        
        self.logger.info(f"\nProcessing complete! {files_processed} files were enhanced, {files_skipped} files were skipped.")

if __name__ == "__main__":
    # Set up paths
    source_dir = r"c:\git\prompts\scraped\poznaj_madar\blog_posts"
