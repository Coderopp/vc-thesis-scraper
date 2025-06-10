# New file: src/notion_integration.py
import requests
from notion_client import Client
import hashlib
from datetime import datetime
from typing import Dict, List, Optional
import re
import logging

logger = logging.getLogger(__name__)

class NotionVCDatabase:
    def __init__(self, notion_token: str, database_id: str):
        self.notion = Client(auth=notion_token)
        self.database_id = database_id
        
    def _generate_hash(self, content: str) -> str:
        """Generate a hash for content deduplication"""
        return hashlib.md5(content.encode()).hexdigest()
        
    def _extract_themes(self, content: str) -> List[Dict]:
        """Extract investment themes from content"""
        theme_keywords = {
            'AI/ML': ['artificial intelligence', 'machine learning', 'AI', 'ML', 'deep learning', 'neural network'],
            'Fintech': ['fintech', 'financial', 'payments', 'banking', 'lending', 'insurance'],
            'Healthcare': ['healthcare', 'health', 'medical', 'biotech', 'pharma', 'telemedicine'],
            'SaaS': ['saas', 'software as a service', 'cloud', 'enterprise software'],
            'E-commerce': ['ecommerce', 'e-commerce', 'retail', 'marketplace', 'shopping'],
            'EdTech': ['edtech', 'education', 'learning', 'online courses', 'training'],
            'Gaming': ['gaming', 'games', 'esports', 'mobile games'],
            'Mobility': ['mobility', 'transportation', 'logistics', 'delivery', 'ride-sharing'],
            'Crypto/Web3': ['crypto', 'blockchain', 'web3', 'defi', 'nft'],
            'Developer Tools': ['developer tools', 'devtools', 'API', 'infrastructure', 'platform']
        }
        
        content_lower = content.lower()
        detected_themes = []
        
        for theme, keywords in theme_keywords.items():
            if any(keyword.lower() in content_lower for keyword in keywords):
                detected_themes.append({"name": theme})
                
        return detected_themes if detected_themes else [{"name": "General"}]
        
    def _extract_company_name(self, title: str, content: str) -> str:
        """Extract company name from title or content"""
        # Common patterns for company names in investment announcements
        patterns = [
            r'investment in ([A-Z][a-zA-Z\s]+)',
            r'backing ([A-Z][a-zA-Z\s]+)',
            r'funding ([A-Z][a-zA-Z\s]+)',
            r'"([A-Z][a-zA-Z\s]+)"',
            r'partnering with ([A-Z][a-zA-Z\s]+)',
        ]
        
        text = f"{title} {content[:500]}"
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                company = match.group(1).strip()
                # Filter out common false positives
                if len(company) > 2 and company.lower() not in ['the', 'and', 'our', 'new', 'this']:
                    return company
                    
        return "Unknown"

    def create_article_page(self, article: Dict) -> str:
        """Create a new page in Notion database for an article"""
        try:
            company_name = self._extract_company_name(article.get('title', ''), article.get('content', ''))
            
            properties = {
                "Title": {"title": [{"text": {"content": article.get('title', 'Untitled')[:100]}}]},
                "VC Firm": {"select": {"name": article.get('vc_name', 'Unknown')}},
                "URL": {"url": article.get('url', '')},
                "Date": {"date": {"start": article.get('date', datetime.now().isoformat().split('T')[0])}},
                "Content Hash": {"rich_text": [{"text": {"content": self._generate_hash(article.get('content', ''))}}]},
                "Status": {"select": {"name": "New"}},
                "Investment Theme": {"multi_select": self._extract_themes(article.get('content', ''))},
                "Company": {"rich_text": [{"text": {"content": company_name}}]},
                "Source": {"select": {"name": "Auto-Scraped"}}
            }
            
            # Create the page with content blocks
            content_blocks = []
            content = article.get('content', '')
            
            # Split content into chunks for Notion blocks (max 2000 chars per block)
            chunk_size = 1900
            for i in range(0, len(content), chunk_size):
                chunk = content[i:i + chunk_size]
                if chunk.strip():
                    content_blocks.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": chunk}}]
                        }
                    })
            
            # Add URL as a link block
            if article.get('url'):
                content_blocks.insert(0, {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{
                            "type": "text",
                            "text": {"content": f"Source: {article['url']}"},
                            "annotations": {"bold": True}
                        }]
                    }
                })
            
            page = self.notion.pages.create(
                parent={"database_id": self.database_id},
                properties=properties,
                children=content_blocks[:10]  # Limit to 10 blocks to avoid API limits
            )
            
            logger.info(f"Created Notion page for: {article.get('title', 'Untitled')[:50]}")
            return page['id']
            
        except Exception as e:
            logger.error(f"Error creating Notion page: {e}")
            raise
    
    def check_article_exists(self, content_hash: str) -> bool:
        """Check if article already exists in database"""
        try:
            response = self.notion.databases.query(
                database_id=self.database_id,
                filter={
                    "property": "Content Hash",
                    "rich_text": {"equals": content_hash}
                }
            )
            return len(response['results']) > 0
        except Exception as e:
            logger.error(f"Error checking article existence: {e}")
            return False
            
    def get_recent_articles(self, days: int = 7) -> List[Dict]:
        """Get articles from the last N days"""
        from datetime import datetime, timedelta
        
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat().split('T')[0]
        
        try:
            response = self.notion.databases.query(
                database_id=self.database_id,
                filter={
                    "property": "Date",
                    "date": {"on_or_after": cutoff_date}
                },
                sorts=[{"property": "Date", "direction": "descending"}]
            )
            
            articles = []
            for page in response['results']:
                props = page['properties']
                article = {
                    'id': page['id'],
                    'title': props.get('Title', {}).get('title', [{}])[0].get('text', {}).get('content', ''),
                    'vc_name': props.get('VC Firm', {}).get('select', {}).get('name', ''),
                    'url': props.get('URL', {}).get('url', ''),
                    'date': props.get('Date', {}).get('date', {}).get('start', ''),
                    'themes': [theme['name'] for theme in props.get('Investment Theme', {}).get('multi_select', [])],
                    'company': props.get('Company', {}).get('rich_text', [{}])[0].get('text', {}).get('content', '')
                }
                articles.append(article)
                
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching recent articles: {e}")
            return []
            
    def update_article_status(self, page_id: str, status: str):
        """Update the status of an article"""
        try:
            self.notion.pages.update(
                page_id=page_id,
                properties={
                    "Status": {"select": {"name": status}}
                }
            )
            logger.info(f"Updated article status to: {status}")
        except Exception as e:
            logger.error(f"Error updating article status: {e}")