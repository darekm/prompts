import os
import requests
from bs4 import BeautifulSoup
import time
import datetime
import re
import yaml

from urllib.parse import urljoin


class BlogScraper:
    def __init__(self, logger,base_url, output_dir):
        self.logger = logger
        self.base_url = base_url
        self.output_dir = output_dir
        self.session = requests.Session()
        self.processed_urls = set()
        self.post_urls = set()
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(os.path.join(output_dir, "blog_posts"), exist_ok=True)
    
    def fetch_page(self, url):
        """Fetch a page with proper headers and error handling"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        }
        
        try:
            response = self.session.get(url, headers=headers)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            self.logger.error(f"Error fetching {url}: {e}")
            return None
    
    def is_post_url(self, url):
        """Determine if a URL is likely a blog post"""
        # Blogspot post URLs typically contain /year/month/post-title.html
        post_pattern = re.compile(r'\d{4}/\d{2}/[^/]+\.html')
        return bool(post_pattern.search(url))
    
    def extract_blog_posts(self, html_content, page_url):
        """Extract blog post URLs from the blog page"""
        if not html_content:
            return []
        
        soup = BeautifulSoup(html_content, 'html.parser')
        blog_posts = []
        
        # Approach 1: Look for specific Blogger post links
        post_titles = soup.select('.post-title a, .entry-title a, h3.post-title a')
        for link in post_titles:
            if link.has_attr('href'):
                post_url = urljoin(self.base_url, link['href'])
                if self.is_post_url(post_url) and post_url not in self.post_urls:
                    blog_posts.append(post_url)
                    self.post_urls.add(post_url)
        
        # Approach 2: Look in the blog archive widgets
        archive_links = soup.select('.BlogArchive a, #BlogArchive1 a, .archive-list a')
        for link in archive_links:
            if link.has_attr('href'):
                href = link['href']
                url = urljoin(self.base_url, href)
                if self.is_post_url(url) and url not in self.post_urls:
                    blog_posts.append(url)
                    self.post_urls.add(url)
        
        # Approach 3: Generic approach for any links that match post pattern
        for link in soup.find_all('a', href=True):
            href = link['href']
            url = urljoin(self.base_url, href)
            if self.is_post_url(url) and url not in self.post_urls:
                blog_posts.append(url)
                self.post_urls.add(url)
        
        return blog_posts
    
    def find_next_page(self, html_content, current_url):
        """Find pagination links to next pages"""
        if not html_content:
            return None
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Look for Blogger's "Older Posts" or pagination links
        next_links = soup.select('.blog-pager-older-link, a.blog-pager-older-link, #Blog1_blog-pager-older-link')
        if next_links and next_links[0].has_attr('href'):
            return urljoin(self.base_url, next_links[0]['href'])
        
        # Alternative: Look for any links containing "older", "next", etc.
        next_candidates = soup.select('a[href*="pageToken="], a.next, a:contains("Older"), a:contains("Next")')
        for link in next_candidates:
            if link.has_attr('href'):
                return urljoin(self.base_url, link['href'])
        
        # Try to find links to month archives
        archive_links = soup.select('.BlogArchive a, #BlogArchive1 a')
        archive_urls = []
        for link in archive_links:
            if link.has_attr('href'):
                url = urljoin(self.base_url, link['href'])
                if url not in self.processed_urls and '/search?' in url:
                    archive_urls.append(url)
        
        return archive_urls if archive_urls else None
    
    def find_outer_element(self, element):
        """Find the outermost element containing a specific tag"""
        parent = element

        while parent and parent.name in ['span','u','b'] :
            parent = parent.parent
        return parent
    def extract_content(self, html_content, url):
        """Extract relevant content from a blog post"""
        if not html_content:
            return None
        
        soup = BeautifulSoup(html_content, 'html.parser')
        # Print all elements of soup with a class attribute
        elements_with_class = soup.find_all(class_=True)
        for element in elements_with_class:
            print(element)
        # Extract title
        title_element = soup.select_one('.post-title, .entry-title')
        if not title_element:
            title_element = soup.find('h1') or soup.find('h2') or soup.find('title')
        title = title_element.get_text().strip() if title_element else "Untitled Post"
        
        # Extract date
        date = None
        date_element = soup.select_one('.date-header, .post-timestamp, .published, time, .date-outer')
        if date_element:
            date_text = date_element.get_text().strip()
            try:
                # Try to parse different date formats
                for fmt in ['%B %d, %Y', '%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%A, %B %d, %Y']:
                    try:
                        date = datetime.datetime.strptime(date_text, fmt).strftime('%Y-%m-%d')
                        break
                    except ValueError:
                        continue
            except Exception:
                pass
        
        if not date:
            # Try to extract date from URL
            match = re.search(r'(\d{4})/(\d{2})', url)
            if match:
                year, month = match.groups()
                date = f"{year}-{month}-01"  # Default to first day of month
            else:
                # Use current date as fallback
                date = datetime.datetime.now().strftime('%Y-%m-%d')
        
        # Extract author
        author_element = soup.select_one('.author, .post-author, .byline')
        author = author_element.get_text().strip() if author_element else "Unknown Author"
        
        # Extract main content
        content_element = soup.select_one('.post-body, .entry-content, article, .post')
        if not content_element:
            content_element = soup.find('body')
        
        # Extract related links (tematy pokrewne/powiązane)
        related_links = []
        
        # Look specifically for sections with "Tematy pokrewne" or similar labels
        related_headers = []
        for header in soup.find_all(['h2', 'h3', 'h4', 'h5', 'strong', 'b']):
            header_text = header.get_text().lower().strip()
            if any(phrase in header_text for phrase in ['tematy pokrewne', 'tematy powiązane', 'powiązane tematy']):
                    related_headers.append(self.find_outer_element(header))
        # For each related header, extract links that follow it
        for header in related_headers:
            current = header.next_sibling
            while current and not (current.name in ['h2', 'h3', 'h4', 'h5'] and current != header):
                if current.name == 'a' and current.has_attr('href'):
                    related_links.append({
                        'title': current.get_text().strip(),
                        'url': urljoin(self.base_url, current['href'])
                    })
                elif hasattr(current, 'find_all'):
                    for link in current.find_all('a', href=True):
                        related_links.append({
                            'title': link.get_text().strip(),
                            'url': urljoin(self.base_url, link['href'])
                        })
                current = current.next_sibling
        
        
        # Clean up content
        if content_element:
            # Remove unwanted elements
            for element in content_element.select('script, style, nav, header, footer, .comments, .sidebar, .post-share-buttons'):
                if element:
                    element.decompose()
            
            content = content_element.get_text('\n', strip=True)
            
            # Clean up extra whitespace
            content = re.sub(r'\n{3,}', '\n\n', content)
        else:
            content = "Content could not be extracted"
        
        # Extract tags/categories (etykiety)
        tags = []
        tag_elements = soup.select('.post-labels a, .tags a, .categories a, .post-tags a, a[rel="tag"], .labels a')
        
        # Also look for elements containing text 'etykiety' or 'tags'
        # Find label sections with more reliable approach
      
            
        
        # Also check for standard Blogger label classes
        if not tag_elements:
            for label_class in ['.post-labels', '.labels', '.tags', '.categories']:
                label_sections = soup.select(label_class)
                for section in label_sections:
                    for link in section.find_all('a'):
                        tag_elements.append(link)
            
        for tag in tag_elements:
            tag_text = tag.get_text().strip()
            if tag_text and not tag_text.startswith('http'):  # Filter out URLs
                tags.append(tag_text)
        
        return {
            'title': title,
            'date': date,
            'author': author,
            'content': content,
            'tags': tags,
            'related_links': related_links,
            'source_url': url
        }
    
    def save_as_markdown(self, post_data):
        """Save extracted content as Markdown with YAML frontmatter"""
        if not post_data:
            return False
        
        # Create a safe filename from the title
        safe_title = re.sub(r'[^\w\s-]', '', post_data['title']).strip()
        safe_title = re.sub(r'[-\s]+', '-', safe_title).lower()
        
        # Add date to filename for better organization
        filename = f"{post_data['date']}-{safe_title[:50]}.md"
        filepath = os.path.join(self.output_dir, "blog_posts", filename)
        
        # Prepare YAML frontmatter
        frontmatter = {
            'title': post_data['title'],
            'date': post_data['date'],
            'author': post_data['author'],
            'tags': post_data['tags'],
            'source_url': post_data['source_url'],
            'type': 'blog_post'
        }
        
        # Add related links if they exist
        if post_data.get('related_links') and len(post_data['related_links']) > 0:
            frontmatter['related_links'] = post_data['related_links']
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                # Write YAML frontmatter between triple dashes
                f.write('---\n')
                yaml.dump(frontmatter, f, default_flow_style=False)
                f.write('---\n\n')
                
                # Write content
                f.write(post_data['content'])
            
            self.logger.info(f"Saved: {filename}")
            return True
        except Exception as e:
            self.logger.error(f"Error saving {filename}: {e}")
            return False
    
    def discover_posts_from_main_page(self):
        """Get posts and pagination from the main blog page"""
        self.logger.info(f"Discovering posts from main page: {self.base_url}")
        
        # Fetch main page
        main_page = self.fetch_page(self.base_url)
        if not main_page:
            self.logger.error(f"Could not fetch main page: {self.base_url}")
            return 0
        
        self.processed_urls.add(self.base_url)
        main_posts = self.extract_blog_posts(main_page, self.base_url)
        self.logger.info(f"Found {len(main_posts)} posts on main page")

        return len(self.post_urls)
    
    def discover_posts_from_pagination(self):
        # Follow pagination
        current_url = self.base_url
        page_num = 1
        istart=len(self.post_urls)
        
        while current_url and page_num < 100:  # Safety limit
            if page_num > 1:
                self.logger.info(f"Checking pagination page {page_num}: {current_url}")
                page_html = self.fetch_page(current_url)
                
                if not page_html:
                    break
                    
                self.processed_urls.add(current_url)
                
                # Extract posts from this page
                page_posts = self.extract_blog_posts(page_html, current_url)
                self.logger.info(f"Found {len(page_posts)} posts on page {page_num}")
                
                # Get next page link
                next_url = self.find_next_page(page_html, current_url)
                
                # If we got archive links instead of regular pagination,
                # we'll handle them separately
                if isinstance(next_url, list):
                    break
                
                current_url = next_url
            
            page_num += 1
            time.sleep(2)
        
        return len(self.post_urls)-istart

    def discover_posts_from_archives(self):
        """Find posts by browsing through archive pages"""
        self.logger.info("Discovering posts from archive pages...")
        
        # Blogspot archive search pattern
        archive_base = f"{self.base_url}/search"
        current_year = datetime.datetime.now().year
        year_count = 0
        
        # Check archives by year
        for year in range(current_year, 2004, -1):  # Most blogs won't be older than 2005
            year_url = f"{archive_base}?updated-min={year}-01-01T00:00:00&updated-max={year+1}-01-01T00:00:00"
            
            self.logger.info(f"Checking year archive: {year}")
            year_html = self.fetch_page(year_url)
            
            if not year_html:
                continue
                
            self.processed_urls.add(year_url)
            year_posts = self.extract_blog_posts(year_html, year_url)
            
            if year_posts:
                self.logger.info(f"Found {len(year_posts)} posts from {year}")
                year_count += 1
            else:
                # If we find two consecutive years with no posts, we can likely stop
                if year_count > 0:
                    break
                continue
            
            # Check if archive has pagination
            next_page = self.find_next_page(year_html, year_url)
            
            # Process archive links if found
            if isinstance(next_page, list):
                for archive_url in next_page:
                    if archive_url not in self.processed_urls:
                        self.logger.info(f"Checking archive: {archive_url}")
                        self.processed_urls.add(archive_url)
                        archive_html = self.fetch_page(archive_url)
                        
                        if archive_html:
                            archive_posts = self.extract_blog_posts(archive_html, archive_url)
                            if archive_posts:
                                self.logger.info(f"Found {len(archive_posts)} posts from archive")
                        time.sleep(1)
            
            # Only check individual months if we've found relatively few posts for the year
            if len(year_posts) < 20:
                self.check_monthly_archives(year)
            
            time.sleep(2)
        
        return len(self.post_urls)
    
    def check_monthly_archives(self, year):
        """Check monthly archives for a specific year"""
        archive_base = f"{self.base_url}/search"
        
        for month in range(1, 13):
            # Calculate next month for date range (handle December correctly)
            next_month = month + 1 if month < 12 else 1
            next_month_year = year if month < 12 else year + 1
            
            month_url = f"{archive_base}?updated-min={year}-{month:02d}-01T00:00:00&updated-max={next_month_year}-{next_month:02d}-01T00:00:00"
            
            if month_url in self.processed_urls:
                continue
                
            self.logger.info(f"Checking month archive: {year}-{month:02d}")
            month_html = self.fetch_page(month_url)
            
            if month_html:
                self.processed_urls.add(month_url)
                month_posts = self.extract_blog_posts(month_html, month_url)
                
                if month_posts:
                    self.logger.info(f"Found {len(month_posts)} posts in {year}-{month:02d}")
            
            time.sleep(1)
    
    def extract_posts(self):
        """Process all discovered post URLs and save them as markdown"""
        total_posts = len(self.post_urls)
        
        if total_posts == 0:
            self.logger.warning("No posts found to process")
            return 0
            
        self.logger.info(f"Processing {total_posts} discovered posts")
        posts_processed = 0
        
        # Convert set to list for tracking progress
        post_list = list(self.post_urls)
        
        for i, url in enumerate(post_list):
            self.logger.info(f"Processing post {i+1}/{total_posts}: {url}")
            
            # Fetch and process the post
            post_html = self.fetch_page(url)
            if not post_html:
                self.logger.warning(f"Could not fetch post: {url}")
                continue
                
            # Extract and save content
            post_data = self.extract_content(post_html, url)
            if post_data and self.save_as_markdown(post_data):
                posts_processed += 1
                self.logger.info(f"Successfully saved post {posts_processed}/{total_posts}")
            
            # Be respectful to the server
            time.sleep(2)
        
        return posts_processed
    
    def scrape_blog(self):
        """Main function to scrape the blog with improved structure"""
        self.logger.info(f"Starting blog scraping for {self.base_url}")
        
        # Step 1: Discover posts from main page and pagination
        io=self.discover_posts_from_main_page()
        self.logger.info(f"Scraping from main {io} unique posts.")
        io=self.discover_posts_from_pagination()
        self.logger.info(f"Scraping pagination {io} unique posts.")
        
        # Step 2: If we need more posts, check the archives
        if len(self.post_urls) < 100:  # Only check archives if we don't have many posts yet
            self.discover_posts_from_archives()
        self.logger.info(f"Scraping completed. Found {len(self.post_urls)} unique posts.")
        
        # Step 3: Process all discovered posts
        processed_count = self.extract_posts()
        
        # Summarize results
        self.logger.info(f"Successfully processed and saved {processed_count} posts.")
        
        return processed_count

    def scrape_main(self):
        """Main function to scrape the blog with improved structure"""
        self.logger.info(f"Starting blog-main scraping for {self.base_url}")
        
        # Step 1: Discover posts from main page and pagination
        self.discover_posts_from_main_page()
        
        # Step 2: If we need more posts, check the archives
        self.logger.info(f"Scraping completed. Found {len(self.post_urls)} unique posts.")
        
        # Step 3: Process all discovered posts
        processed_count = self.extract_posts()
        
        # Summarize results
        self.logger.info(f"Successfully processed and saved {processed_count} posts.")
        
        return processed_count

if __name__ == "__main__":
    # Using the provided URL 
    blog_url = "https://invoicer.blogspot.com"
    output_directory = os.path.join("c:\\git\\prompts", "scraped", "invoicer_blogspot")
    
    #scraper = BlogScraper(blog_url, output_directory)
    #scraper.scrape_blog()
