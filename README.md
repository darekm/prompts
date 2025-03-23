# Prompts

## Knowledge Database Architecture

This project builds a comprehensive knowledge database from websites, documents, and emails.

### System Components

1. **Data Collection Layer**
   - Web Crawlers and Scrapers
   - Document Parsers (PDF, Office, etc.)
   - Email Connectors (IMAP, Exchange, API)
   - API Integrations

2. **Data Processing Pipeline**
   - Content Extraction
   - Text Normalization
   - Language Detection
   - Entity Recognition
   - Document Classification
   - Duplicate Detection
   - Content Summarization

3. **Storage Layer**
   - Document Store (raw documents)
   - Vector Store (embeddings)
   - Metadata Store (attributes, tags)
   - Knowledge Graph (relationships)

4. **Search & Retrieval Layer**
   - Full-text Search
   - Semantic Search
   - Query Processing
   - Relevance Ranking
   - Result Filtering

5. **Application Layer**
   - API Services
   - User Interface
   - Authentication & Authorization
   - User Management
   - Analytics Dashboard

### Data Flow

```
[Data Sources] → [Collection Layer] → [Processing Pipeline] → [Storage Layer]
                                                                    ↓
                    [Users/Applications] ← [Application Layer] ← [Search & Retrieval]
```

### Technology Stack

- **Data Collection**: Scrapy, Beautiful Soup, Apache Tika, MS Graph API
- **Processing**: spaCy, NLTK, Hugging Face Transformers, LangChain
- **Storage**: Elasticsearch, PostgreSQL, Neo4j, Milvus/FAISS
- **Application**: FastAPI/Django, React/Vue.js
- **Infrastructure**: Docker, Kubernetes, AWS/Azure/GCP

### Implementation Phases

1. **Phase 1**: Core infrastructure and basic data collection
2. **Phase 2**: Processing pipeline and storage implementation
3. **Phase 3**: Search functionality and basic UI
4. **Phase 4**: Advanced features and integrations

# Content Scrapers

## Simple Blog Scraper

A simple utility to scrape blog content and save it in markdown format suitable for processing with LLMs.

### Setup

1. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

2. Run the scraper:
   ```
   python blog_scraper.py
   ```

### Output Format

The scraper saves blog posts as markdown files with YAML frontmatter in the `scraped_content/blog_posts` directory. Each file includes:

#### Frontmatter (for metadata)
- title: The blog post title
- date: Publication date
- author: Post author
- tags: Categories or tags
- source_url: Original URL
- type: Content type (blog_post)

### Content
The main body text is stored as plain markdown text below the frontmatter.

## Crawl4all Scraper

An advanced web scraper using Crawl4all for more efficient and comprehensive content extraction.

### Setup

1. Install Crawl4all:
   ```
   pip install crawl4all
   ```

2. Run the advanced scraper:
   ```
   python crawl4all_scraper.py
   ```

### Features

- Efficient crawling with proper rate limiting
- Comprehensive metadata extraction
- Robust content detection and cleaning
- Advanced date and author extraction
- Configurable crawl depth and patterns
- Better organization of output files

### LLM Processing

This format makes it easy for LLMs to:
- Extract structured metadata from the YAML frontmatter
- Process the content text
- Understand the relationship between different posts via tags
- Maintain source attribution

## Notes

- Both scrapers include appropriate delays between requests to avoid overwhelming target sites
- Adjust the selectors in the extraction methods if the site has a unique structure