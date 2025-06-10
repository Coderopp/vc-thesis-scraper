# New file: src/automated_monitor.py
import schedule
import time
from datetime import datetime, timedelta
from enhanced_scraper import EnhancedMultiVCScraper

class VCMonitoringService:
    def __init__(self, notion_token: str, database_id: str):
        self.scraper = EnhancedMultiVCScraper(notion_token, database_id)
        
    def daily_scan(self):
        """Daily scan for new articles"""
        logger.info("Starting daily VC article scan...")
        
        # Scrape all VCs
        articles = self.scraper.scrape_all_vcs(max_articles_per_vc=20)
        
        # Process and store
        stats = self.scraper.process_and_store_articles(articles)
        
        # Send notification if new articles found
        if stats["new"] > 0:
            self.send_notification(stats)
            
    def send_notification(self, stats: Dict):
        """Send notification about new articles"""
        # Could integrate with Slack, email, etc.
        pass
        
    def start_monitoring(self):
        """Start the automated monitoring"""
        schedule.every().day.at("09:00").do(self.daily_scan)
        schedule.every().day.at("17:00").do(self.daily_scan)
        
        while True:
            schedule.run_pending()
            time.sleep(3600)  # Check every hour