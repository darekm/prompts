import os
import json
import yaml
import logging
import subprocess
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Crawl4AllScraper:
    """Scraper implementation using Crawl4all for more efficient crawling"""
    
    def __init__(self, base_url, output_dir, crawl4all_path=None, max_depth=3, delay=1):
        """
        Initialize the Crawl4all scraper
        
        Args:
            base_url: The starting URL for crawling
            output_dir: Directory to save the extracted content
            crawl4all_path: Path to the Crawl4all executable (if None, assumes it's in PATH)
            max_depth: Maximum crawl depth from base URL
            delay: Delay between requests in seconds
        """
        self.base_url = base_url
        self.output_dir = output_dir
        self.domain = urlparse(base_url).netloc
        self.crawl4all_path = crawl4all_path or "crawl4all"
        self.max_depth = max_depth
        self.delay = delay
        self.config_file = os.path.join(output_dir, f"{self.domain}_crawl_config.json")
        self.crawl_output_dir = os.path.join(output_dir, "crawl_data")
        self.processed_dir = os.path.join(output_dir, "processed_content")
        
        # Create output directories
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(self.crawl_output_dir, exist_ok=True)
        os.makedirs(self.processed_dir, exist_ok=True)
        os.makedirs(os.path.join(self.processed_dir, "blog_posts"), exist_ok=True)

    def _create_crawl_config(self):
        """Create a configuration file for Crawl4all"""
        config = {
            "name": f"crawl_{self.domain}",
            "start_urls": [self.base_url],
            "allowed_domains": [self.domain],
            "max_depth": self.max_depth,
            "follow_redirects": True,
            "respect_robots_txt": True,
            "download_delay": self.delay,
            "concurrent_requests": 2,
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "output_dir": self.crawl_output_dir,
            "save_html": True,
            "extract_text": True,
            "extract_links": True,
            "extract_metadata": True,
            # Custom URL patterns to identify blog posts (adjust for specific site)
            "url_patterns": {
                "blog_post": [
                    ".*/(19|20)\\d{2}/\\d{1,2}/[^/]+\\.html",
                    ".*/p/[^/]+\\.html",
                    ".*/blog/[^/]+",
                    ".*/posts/[^/]+"
                ]
            }
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"Created crawl configuration at {self.config_file}")
        return self.config_file

    def run_crawler(self):
        """Run the Crawl4all crawler with the configured settings"""
        config_path = self._create_crawl_config()
        
        try:
            logger.info(f"Starting Crawl4all crawler for {self.base_url}")
            cmd = [self.crawl4all_path, "crawl", "--config", config_path]
            
            # Run the crawler
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True
            )
            
            # Display crawler output in real-time
            for line in process.stdout:
                logger.info(f"Crawl4all: {line.strip()}")
            
            process.wait()
            
            if process.returncode != 0:
                error = process.stderr.read()
                logger.error(f"Crawler failed: {error}")
                return False
                
            logger.info(f"Crawler completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error running crawler: {e}")
            return False

    def process_crawled_pages(self):
        """Process pages collected by the crawler and convert to markdown"""
        # Load the crawl index (created by Crawl4all)
        index_file = os.path.join(self.crawl_output_dir, "index.json")
        
        if not os.path.exists(index_file):
            logger.error(f"Crawl index file not found at {index_file}")
            return 0
            
        with open(index_file, 'r') as f:
            crawl_index = json.load(f)
        
        if not crawl_index.get("pages"):
            logger.warning("No pages found in crawl index")
            return 0
            
        # Count of blog posts processed
        processed_count = 0
        
        # Process each page
        for page_id, page_info in crawl_index["pages"].items():
            url = page_info.get("url")
            content_file = page_info.get("content_file")
            page_type = page_info.get("type", "")
            
            # Skip non-blog pages based on URL patterns or crawler classification
            if not self._is_blog_post(url, page_type):
                continue
                
            # Get the HTML content
            html_path = os.path.join(self.crawl_output_dir, content_file)
            if not os.path.exists(html_path):
                logger.warning(f"Content file not found: {html_path}")
                continue
            
            # Extract content and metadata
            try:
                with open(html_path, 'r', encoding='utf-8', errors='replace') as f:
                    html_content = f.read()
                    
                # Extract content from HTML
                post_data = self._extract_content(html_content, url)
                
                if post_data:
                    # Save as markdown
                    if self._save_as_markdown(post_data):
                        processed_count += 1
                        logger.info(f"Processed blog post: {post_data['title']}")
            except Exception as e:
                logger.error(f"Error processing {url}: {e}")
        
        logger.info(f"Completed processing {processed_count} blog posts")
        return processed_count
        
    def _is_blog_post(self, url, page_type):
        """
        Determine if a URL is a blog post based on URL pattern and page type
        
        Args:
            url: The URL to check
            page_type: Page type from crawler (if available)
        """
        # Check if crawler already classified it as a blog post
        if page_type == "blog_post":
            return True
            
        # Check common blog post URL patterns
        import re
        patterns = [
            r'/(19|20)\d{2}/\d{1,2}/[^/]+\.html',  # Typical date-based blog URLs
            r'/p/[^/]+\.html',                     # Common Blogger pattern
            r'/posts?/[^/]+',                      # Common blog URL format
            r'/blog/[^/]+',                        # Another common blog pattern
            r'/article[s]?/[^/]+'                  # Article pattern
        ]
        
        for pattern in patterns:
            if re.search(pattern, url):
                return True
                
        return False
    
    def _extract_content(self, html_content, url):
        """
        Extract blog content from HTML
        
        Args:
            html_content: The HTML content of the page
            url: The URL of the page
        """
        if not html_content:
            return None
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract title
        title_element = soup.select_one('.post-title, .entry-title, article h1, .article-title')
        if not title_element:
            title_element = soup.find('h1') or soup.find('h2') or soup.find('title')
        title = title_element.get_text().strip() if title_element else "Untitled Post"
        
        # Extract date
        date = None
        date_selectors = [
            '.date-header', '.post-timestamp', '.published', 'time', 
            '.date-outer', '.post-date', '.entry-date', '.article-date',
            'meta[property="article:published_time"]'
        ]
        
        for selector in date_selectors:
            date_element = soup.select_one(selector)
            if date_element:
                # Check if it's a meta tag
                if date_element.name == 'meta' and date_element.get('content'):
                    date = self._parse_date(date_element['content'])
                    break
                else:
                    date = self._parse_date(date_element.get_text().strip())
                    if date:
                        break
        
        if not date:
            # Try to extract date from URL
            import re
            match = re.search(r'(\d{4})/(\d{2})', url)
            if match:
                year, month = match.groups()
                date = f"{year}-{month}-01"  # Default to first day of month
            else:
                # Use current date as fallback
                date = datetime.now().strftime('%Y-%m-%d')
        
        # Extract author
        author_element = soup.select_one('.author, .post-author, .byline, .entry-author')
        author = author_element.get_text().strip() if author_element else "Unknown Author"
        
        # Extract main content
        content_selectors = [
            '.post-body', '.entry-content', 'article', '.post', 
            '.article-content', '.content', '.blog-content'
        ]
        
        content_element = None
        for selector in content_selectors:
            content_element = soup.select_one(selector)
            if content_element:
                break
                
        if not content_element:
            content_element = soup.find('body')
        
        # Clean up content
        if content_element:
            # Remove unwanted elements
            for element in content_element.select('script, style, nav, header, footer, .comments, .sidebar, .post-share-buttons, .post-footer, .social-share, .related-posts'):
                if element:
                    element.decompose()
            
            content = content_element.get_text('\n', strip=True)
            
            # Clean up extra whitespace
            import re
            content = re.sub(r'\n{3,}', '\n\n', content)
        else:
            content = "Content could not be extracted"
        
        # Extract tags/categories
        tags = []
        tag_selectors = ['.post-labels a', '.tags a', '.categories a', '.post-tags a', '.article-tags a']
        
        for selector in tag_selectors:
            tag_elements = soup.select(selector)
            for tag in tag_elements:
                tags.append(tag.get_text().strip())
        
        return {
            'title': title,
            'date': date,
            'author': author,
            'content': content,
            'tags': tags,
            'source_url': url
        }

    def _parse_date(self, date_str):
        """Parse date string into consistent YYYY-MM-DD format"""
        formats = [
            '%B %d, %Y',          # January 1, 2022
            '%Y-%m-%d',           # 2022-01-01
            '%d/%m/%Y',           # 01/01/2022
            '%m/%d/%Y',           # 01/01/2022
            '%A, %B %d, %Y',      # Monday, January 1, 2022
            '%Y-%m-%dT%H:%M:%S',  # 2022-01-01T12:00:00
            '%Y-%m-%dT%H:%M:%SZ', # 2022-01-01T12:00:00Z
            '%d-%m-%Y',           # 01-01-2022
            '%d %B %Y'            # 01 January 2022
        ]
        
        for fmt in formats:
            try:
                parsed = datetime.strptime(date_str, fmt)
                return parsed.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        return None

    def _save_as_markdown(self, post_data):
        """Save extracted content as Markdown with YAML frontmatter"""
        if not post_data:
            return False
        
        # Create a safe filename from the title
        import re
        safe_title = re.sub(r'[^\w\s-]', '', post_data['title']).strip()
        safe_title = re.sub(r'[-\s]+', '-', safe_title).lower()
        
        # Add date to filename for better organization
        filename = f"{post_data['date']}-{safe_title[:50]}.md"
        filepath = os.path.join(self.processed_dir, "blog_posts", filename)
        
        # Prepare YAML frontmatter
        frontmatter = {
            'title': post_data['title'],
            'date': post_data['date'],
            'author': post_data['author'],
            'tags': post_data['tags'],
            'source_url': post_data['source_url'],
            'type': 'blog_post',
            'scraper': 'crawl4all'
        }
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                # Write YAML frontmatter between triple dashes
                f.write('---\n')
                yaml.dump(frontmatter, f, default_flow_style=False)
                f.write('---\n\n')
                
                # Write content
                f.write(post_data['content'])
            
            logger.info(f"Saved: {filename}")
            return True
        except Exception as e:
            logger.error(f"Error saving {filename}: {e}")
            return False
    
    def scrape_website(self):
        """Main function to scrape the website using Crawl4all"""
        logger.info(f"Starting to scrape {self.base_url} using Crawl4all")
        
        # Step 1: Run the crawler
        if not self.run_crawler():
            logger.error("Crawler failed, cannot continue")
            return 0
        
        # Step 2: Process the crawled content
        processed_count = self.process_crawled_pages()
        
        logger.info(f"Scraping completed. Successfully processed {processed_count} pages")
        return processed_count


if __name__ == "__main__":
    # Example usage
    blog_url = "https://invoicer.blogspot.com"
    output_directory = os.path.join("c:\\git\\prompts", "crawl4al", "invoicer_blogspot")
    
    # Assuming Crawl4all is available in PATH or specify path as below
    # crawl4all_path = "c:\\path\\to\\crawl4all"
    
    scraper = Crawl4AllScraper(blog_url, output_directory)
    scraper.scrape_website()
