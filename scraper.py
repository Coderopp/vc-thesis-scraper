import requests
from bs4 import BeautifulSoup
import pandas as pd
import yaml
import time
import logging
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import hashlib
from utils import clean_article_text

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VCBlogScraper:
    def __init__(self, config_file='vc_sources.yaml', delay=2):
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; VC-Thesis-Bot/1.0)'
        })
        self.results = []
        self.seen_urls = set()
        
        # Load VC sources
        with open(config_file, 'r') as f:
            self.vc_sources = yaml.safe_load(f)['vc_sources']
    
    def can_fetch(self, url):
        """Check if we can fetch the URL according to robots.txt"""
        try:
            parsed_url = urlparse(url)
            robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
            rp = RobotFileParser()
            rp.set_url(robots_url)
            rp.read()
            return rp.can_fetch('*', url)
        except:
            return True  # If we can't check robots.txt, assume it's OK
    
    def is_relevant_link(self, href, vc_config):
        """Check if a link is relevant based on keywords and patterns"""
        if not href:
            return False
        
        href_lower = href.lower()
        
        # Get keywords from config or use defaults
        keywords = vc_config.get('keywords', ['blog', 'thesis', 'memo', 'insight', 'portfolio', 'investment'])
        exclude_keywords = vc_config.get('exclude_keywords', ['contact', 'team', 'about', 'careers', 'privacy'])
        
        # Check if any keyword is in the URL
        has_keyword = any(keyword in href_lower for keyword in keywords)
        
        # Check if any exclude keyword is in the URL
        has_exclude = any(exclude in href_lower for exclude in exclude_keywords)
        
        return has_keyword and not has_exclude
    
    def extract_article_links(self, soup, base_url, vc_config):
        """Extract relevant article links from the page"""
        links = []
        
        # Try different selectors based on VC configuration
        selectors = vc_config.get('article_selectors', [
            'article a', '.post a', '.blog-post a', 
            '.content a', '.insights a', '.news-item a'
        ])
        
        for selector in selectors:
            found_links = soup.select(selector)
            if found_links:
                links.extend(found_links)
        
        # Fallback to all links if no specific selectors work
        if not links:
            links = soup.find_all('a', href=True)
        
        relevant_links = []
        for link in links:
            href = link.get('href', '')
            if self.is_relevant_link(href, vc_config):
                full_url = urljoin(base_url, href)
                title = link.get_text(strip=True) or link.get('title', '')
                
                if full_url not in self.seen_urls and title:
                    relevant_links.append((full_url, title))
                    self.seen_urls.add(full_url)
        
        return relevant_links
    
    def scrape_vc(self, vc_config):
        """Scrape a single VC's blog/news section"""
        vc_name = vc_config['name']
        base_url = vc_config['url']
        
        logger.info(f"Scraping: {vc_name}")
        
        try:
            if not self.can_fetch(base_url):
                logger.warning(f"Robots.txt disallows scraping {base_url}")
                return
            
            resp = self.session.get(base_url, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Extract article links
            article_links = self.extract_article_links(soup, base_url, vc_config)
            logger.info(f"Found {len(article_links)} relevant links for {vc_name}")
            
            # Scrape each article
            for url, title in article_links[:vc_config.get('max_articles', 10)]:
                try:
                    if not self.can_fetch(url):
                        continue
                    
                    logger.info(f"Scraping article: {title[:50]}...")
                    content = clean_article_text(url)
                    
                    if len(content.strip()) > 100:  # Only save if content is substantial
                        # Create a hash to avoid duplicates
                        content_hash = hashlib.md5(content.encode()).hexdigest()
                        
                        self.results.append({
                            "VC Name": vc_name,
                            "Title": title,
                            "URL": url,
                            "Content": content,
                            "Content Hash": content_hash
                        })
                    
                    time.sleep(self.delay)
                    
                except Exception as e:
                    logger.error(f"Error scraping article {url}: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error scraping {vc_name}: {e}")
    
    def scrape_all(self):
        """Scrape all VCs in the configuration"""
        for vc_config in self.vc_sources:
            self.scrape_vc(vc_config)
            time.sleep(self.delay)  # Be respectful between VCs
        
        return self.results
    
    def save_results(self, output_file='output/vc_theses.csv'):
        """Save results to CSV with deduplication"""
        if not self.results:
            logger.warning("No results to save")
            return
        
        df = pd.DataFrame(self.results)
        
        # Remove duplicates based on content hash
        original_count = len(df)
        df = df.drop_duplicates(subset=['Content Hash'])
        df = df.drop(columns=['Content Hash'])  # Remove hash column from final output
        
        logger.info(f"Removed {original_count - len(df)} duplicate articles")
        
        # Create output directory if it doesn't exist
        import os
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        df.to_csv(output_file, index=False)
        logger.info(f"✅ Scraped and saved {len(df)} unique articles to {output_file}")

if __name__ == "__main__":
    scraper = VCBlogScraper()
    scraper.scrape_all()
    scraper.save_results()
