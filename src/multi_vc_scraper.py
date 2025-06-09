import requests
from bs4 import BeautifulSoup
import csv
import time
import random
import logging
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Set
import re
from vc_config import VC_CONFIGS, USER_AGENTS

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MultiVCScraper:
    def __init__(self, delay_range=(1, 3)):
        self.delay_range = delay_range
        self.session = requests.Session()
        self.scraped_urls = set()
        
    def get_random_headers(self) -> Dict[str, str]:
        """Get random headers to avoid detection"""
        return {
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    def make_request(self, url: str) -> requests.Response:
        """Make a request with random delay and headers"""
        headers = self.get_random_headers()
        
        try:
            response = self.session.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Random delay between requests
            delay = random.uniform(*self.delay_range)
            time.sleep(delay)
            
            return response
        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    def extract_links_from_sitemap(self, vc_key: str, vc_config: Dict) -> Set[str]:
        """Extract relevant links from sitemap"""
        sitemap_urls = [
            f"{vc_config['base_url']}/sitemap.xml",
            f"{vc_config['base_url']}/sitemap_index.xml",
            f"{vc_config['base_url']}/robots.txt"
        ]
        
        relevant_links = set()
        
        for sitemap_url in sitemap_urls:
            try:
                response = self.make_request(sitemap_url)
                if not response:
                    continue
                    
                if 'xml' in sitemap_url:
                    soup = BeautifulSoup(response.content, 'xml')
                    urls = [loc.text for loc in soup.find_all('loc')]
                else:  # robots.txt
                    content = response.text
                    sitemap_matches = re.findall(r'Sitemap:\s*(.*)', content)
                    urls = sitemap_matches
                
                for url in urls:
                    if any(pattern in url for pattern in vc_config['search_patterns']):
                        relevant_links.add(url)
                        
            except Exception as e:
                logger.warning(f"Could not process {sitemap_url}: {e}")
                continue
        
        logger.info(f"Found {len(relevant_links)} relevant links for {vc_config['name']}")
        return relevant_links
    
    def extract_links_from_page(self, url: str, vc_config: Dict) -> Set[str]:
        """Extract relevant links from a webpage"""
        response = self.make_request(url)
        if not response:
            return set()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        links = set()
        
        # Find all links on the page
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(url, href)
            
            # Check if link matches search patterns
            if any(pattern in full_url for pattern in vc_config['search_patterns']):
                if urlparse(full_url).netloc == urlparse(vc_config['base_url']).netloc:
                    links.add(full_url)
        
        return links
    
    def discover_links(self, vc_key: str, vc_config: Dict) -> Set[str]:
        """Discover all relevant links for a VC"""
        all_links = set()
        
        # Try sitemap first
        sitemap_links = self.extract_links_from_sitemap(vc_key, vc_config)
        all_links.update(sitemap_links)
        
        # If sitemap didn't yield much, try crawling main pages
        if len(sitemap_links) < 10:
            main_pages = [
                vc_config['base_url'],
                f"{vc_config['base_url']}/blog",
                f"{vc_config['base_url']}/insights",
                f"{vc_config['base_url']}/news",
                f"{vc_config['base_url']}/portfolio"
            ]
            
            for page in main_pages:
                page_links = self.extract_links_from_page(page, vc_config)
                all_links.update(page_links)
        
        return all_links
    
    def extract_content(self, url: str, vc_config: Dict) -> Dict[str, str]:
        """Extract content from a specific URL"""
        if url in self.scraped_urls:
            return None
            
        response = self.make_request(url)
        if not response:
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract title
        title = ""
        for selector in vc_config['content_selectors']['title'].split(', '):
            title_elem = soup.select_one(selector)
            if title_elem:
                title = title_elem.get_text(strip=True)
                break
        
        # Extract content
        content = ""
        for selector in vc_config['content_selectors']['content'].split(', '):
            content_elem = soup.select_one(selector)
            if content_elem:
                # Remove script and style elements
                for script in content_elem(["script", "style"]):
                    script.decompose()
                content = content_elem.get_text(separator=' ', strip=True)
                break
        
        # Extract date
        date = ""
        for selector in vc_config['content_selectors']['date'].split(', '):
            date_elem = soup.select_one(selector)
            if date_elem:
                date = date_elem.get_text(strip=True)
                break
        
        # If no content found, try generic selectors
        if not content:
            generic_selectors = ['main', 'article', '.content', '#content', '.post', '.entry']
            for selector in generic_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    for script in content_elem(["script", "style"]):
                        script.decompose()
                    content = content_elem.get_text(separator=' ', strip=True)
                    break
        
        # Clean up content
        content = re.sub(r'\s+', ' ', content).strip()
        
        if title and content and len(content) > 100:  # Minimum content length
            self.scraped_urls.add(url)
            return {
                'vc_name': vc_config['name'],
                'title': title,
                'url': url,
                'content': content,
                'date': date
            }
        
        return None
    
    def scrape_vc(self, vc_key: str, vc_config: Dict, max_articles: int = 50) -> List[Dict[str, str]]:
        """Scrape articles for a specific VC"""
        logger.info(f"Starting to scrape {vc_config['name']}")
        
        # Discover all relevant links
        links = self.discover_links(vc_key, vc_config)
        logger.info(f"Found {len(links)} potential articles for {vc_config['name']}")
        
        articles = []
        processed = 0
        
        for url in links:
            if len(articles) >= max_articles:
                break
                
            try:
                article = self.extract_content(url, vc_config)
                if article:
                    articles.append(article)
                    logger.info(f"Scraped: {article['title'][:50]}...")
                
                processed += 1
                if processed % 10 == 0:
                    logger.info(f"Processed {processed} URLs for {vc_config['name']}")
                    
            except Exception as e:
                logger.error(f"Error processing {url}: {e}")
                continue
        
        logger.info(f"Successfully scraped {len(articles)} articles from {vc_config['name']}")
        return articles
    
    def scrape_all_vcs(self, vc_list: List[str] = None, max_articles_per_vc: int = 50) -> List[Dict[str, str]]:
        """Scrape articles from multiple VCs"""
        if vc_list is None:
            vc_list = list(VC_CONFIGS.keys())
        
        all_articles = []
        
        for vc_key in vc_list:
            if vc_key not in VC_CONFIGS:
                logger.warning(f"VC '{vc_key}' not found in configuration")
                continue
            
            try:
                vc_config = VC_CONFIGS[vc_key]
                articles = self.scrape_vc(vc_key, vc_config, max_articles_per_vc)
                all_articles.extend(articles)
                
                # Longer delay between VCs
                time.sleep(random.uniform(3, 7))
                
            except Exception as e:
                logger.error(f"Error scraping {vc_key}: {e}")
                continue
        
        return all_articles
    
    def save_to_csv(self, articles: List[Dict[str, str]], filename: str = "output/all_vc_theses.csv"):
        """Save articles to CSV file"""
        if not articles:
            logger.warning("No articles to save")
            return
        
        # Ensure output directory exists
        import os
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['vc_name', 'title', 'url', 'content', 'date']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for article in articles:
                writer.writerow(article)
        
        logger.info(f"Saved {len(articles)} articles to {filename}")

def main():
    """Main function to run the scraper"""
    scraper = MultiVCScraper()
    
    # You can specify which VCs to scrape, or leave None to scrape all
    # vc_list = ["accel", "sequoia", "a16z"]  # Specific VCs
    vc_list = None  # All VCs
    
    # Scrape articles
    articles = scraper.scrape_all_vcs(vc_list=vc_list, max_articles_per_vc=30)
    
    # Save to CSV
    scraper.save_to_csv(articles)
    
    print(f"Scraping completed! Total articles: {len(articles)}")

if __name__ == "__main__":
    main()
