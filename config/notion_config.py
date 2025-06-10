# New file: config/notion_config.py
import os
from dataclasses import dataclass

@dataclass
class NotionConfig:
    token: str = os.getenv('NOTION_TOKEN')
    database_id: str = os.getenv('NOTION_DATABASE_ID')
    
    # Webhook settings for real-time updates
    webhook_url: str = os.getenv('WEBHOOK_URL', '')
    
    # Monitoring settings
    check_interval_hours: int = 6
    max_articles_per_run: int = 50