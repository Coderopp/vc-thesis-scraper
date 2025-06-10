import os
import json
import logging
import hashlib
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Set
from dotenv import load_dotenv
import schedule
import time

from .multi_vc_scraper import EnhancedMultiVCScraper
from .notion_integration import NotionVCDatabase
from config.vc_config import load_vc_configs

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SmartVCMonitor:
    def __init__(self, state_file="data/scraper_state.json", csv_file="output/vc_articles_incremental.csv"):
        load_dotenv()
        
        self.state_file = state_file
        self.csv_file = csv_file
        self.notion_token = os.getenv('NOTION_TOKEN')
        self.database_id = os.getenv('NOTION_DATABASE_ID')
        
        # Initialize components
        self.scraper = EnhancedMultiVCScraper(self.notion_token, self.database_id)
        self.vc_configs = load_vc_configs()
        
        # Ensure directories exist
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        os.makedirs(os.path.dirname(self.csv_file), exist_ok=True)
        
        # Load existing state
        self.state = self.load_state()
        
    def load_state(self) -> Dict:
        """Load previous scraping state to track what's already been processed"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                logger.info(f"Loaded state with {len(state.get('seen_urls', {}))} tracked URLs")
                return state
            except Exception as e:
                logger.warning(f"Could not load state file: {e}")
        
        # Default state structure
        return {
            'seen_urls': {},  # url -> {'hash': content_hash, 'scraped_at': timestamp}
            'last_run': None,
            'total_articles_scraped': 0,
            'vc_stats': {}  # vc_name -> {'last_scraped': timestamp, 'total_articles': count}
        }
    
    def save_state(self):
        """Save current state to file"""
        try:
            self.state['last_run'] = datetime.now().isoformat()
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)
            logger.info("State saved successfully")
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
    
    def generate_content_signature(self, article: Dict) -> str:
        """Generate a unique signature for article content"""
        content = f"{article.get('title', '')}{article.get('url', '')}{article.get('content', '')[:500]}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def is_new_article(self, article: Dict) -> bool:
        """Check if this article is new or has been updated"""
        url = article.get('url', '')
        current_signature = self.generate_content_signature(article)
        
        if url not in self.state['seen_urls']:
            return True
        
        # Check if content has changed
        previous_signature = self.state['seen_urls'][url].get('hash', '')
        return current_signature != previous_signature
    
    def discover_new_links_for_vc(self, vc_config: Dict) -> Set[str]:
        """Discover only new links for a specific VC since last run"""
        vc_key = vc_config['key']
        vc_name = vc_config['name']
        
        logger.info(f"🔍 Checking for new links from {vc_name}")
        
        # Use the existing discovery method but limit scope
        links = self.scraper.discover_links(vc_key, vc_config)
        
        # Filter to only new/unseen URLs
        new_links = set()
        for link in links:
            if link not in self.state['seen_urls']:
                new_links.add(link)
        
        logger.info(f"📊 {vc_name}: {len(links)} total links, {len(new_links)} new links")
        return new_links
    
    def scrape_new_articles_for_vc(self, vc_config: Dict, max_new_articles: int = 20) -> List[Dict]:
        """Scrape only new articles from a specific VC"""
        vc_key = vc_config['key']
        vc_name = vc_config['name']
        
        # Get new links
        new_links = self.discover_new_links_for_vc(vc_config)
        
        if not new_links:
            logger.info(f"✅ No new articles found for {vc_name}")
            return []
        
        new_articles = []
        processed = 0
        
        for url in list(new_links)[:max_new_articles]:  # Limit processing
            try:
                article = self.scraper.extract_content(url, vc_config)
                if article and self.is_new_article(article):
                    new_articles.append(article)
                    
                    # Update state
                    self.state['seen_urls'][url] = {
                        'hash': self.generate_content_signature(article),
                        'scraped_at': datetime.now().isoformat(),
                        'vc_name': vc_name
                    }
                    
                    logger.info(f"📰 NEW: {article['title'][:60]}...")
                
                processed += 1
                if processed % 5 == 0:
                    logger.info(f"Processed {processed}/{len(new_links)} new URLs for {vc_name}")
                    
            except Exception as e:
                logger.error(f"Error processing {url}: {e}")
                continue
        
        # Update VC stats
        if vc_name not in self.state['vc_stats']:
            self.state['vc_stats'][vc_name] = {'total_articles': 0}
        
        self.state['vc_stats'][vc_name]['last_scraped'] = datetime.now().isoformat()
        self.state['vc_stats'][vc_name]['total_articles'] += len(new_articles)
        
        logger.info(f"✅ {vc_name}: Found {len(new_articles)} new articles")
        return new_articles
    
    def run_daily_check(self) -> Dict:
        """Main daily check for new articles across all VCs"""
        start_time = datetime.now()
        logger.info(f"🚀 Starting daily VC monitoring at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        all_new_articles = []
        stats = {
            'total_new': 0,
            'by_vc': {},
            'errors': 0,
            'runtime_minutes': 0
        }
        
        # Check each VC for new articles
        for i, vc_config in enumerate(self.vc_configs, 1):
            vc_name = vc_config['name']
            logger.info(f"[{i}/{len(self.vc_configs)}] Checking {vc_name}...")
            
            try:
                new_articles = self.scrape_new_articles_for_vc(vc_config, max_new_articles=15)
                
                if new_articles:
                    all_new_articles.extend(new_articles)
                    stats['by_vc'][vc_name] = len(new_articles)
                    stats['total_new'] += len(new_articles)
                else:
                    stats['by_vc'][vc_name] = 0
                
                # Small delay between VCs
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"❌ Error checking {vc_name}: {e}")
                stats['errors'] += 1
                stats['by_vc'][vc_name] = 0
        
        # Save new articles
        if all_new_articles:
            self.save_new_articles(all_new_articles)
            
            # Store in Notion if available
            if self.scraper.notion_db:
                notion_stats = self.scraper.process_and_store_articles(all_new_articles)
                logger.info(f"💾 Notion: {notion_stats['new']} new, {notion_stats['existing']} existing")
        
        # Update stats and save state
        end_time = datetime.now()
        stats['runtime_minutes'] = round((end_time - start_time).total_seconds() / 60, 2)
        self.state['total_articles_scraped'] += stats['total_new']
        self.save_state()
        
        # Log summary
        self.log_daily_summary(stats)
        return stats
    
    def save_new_articles(self, new_articles: List[Dict]):
        """Save new articles to CSV (append mode)"""
        if not new_articles:
            return
        
        df_new = pd.DataFrame(new_articles)
        
        # Add timestamp
        df_new['scraped_at'] = datetime.now().isoformat()
        
        # Append to existing CSV or create new one
        if os.path.exists(self.csv_file):
            df_new.to_csv(self.csv_file, mode='a', header=False, index=False)
            logger.info(f"📊 Appended {len(new_articles)} new articles to {self.csv_file}")
        else:
            df_new.to_csv(self.csv_file, index=False)
            logger.info(f"📊 Created {self.csv_file} with {len(new_articles)} articles")
    
    def log_daily_summary(self, stats: Dict):
        """Log a comprehensive daily summary"""
        logger.info("=" * 60)
        logger.info("📋 DAILY MONITORING SUMMARY")
        logger.info("=" * 60)
        logger.info(f"🕐 Runtime: {stats['runtime_minutes']} minutes")
        logger.info(f"📰 Total new articles: {stats['total_new']}")
        logger.info(f"❌ Errors: {stats['errors']}")
        logger.info(f"📊 Total articles tracked: {len(self.state['seen_urls'])}")
        
        if stats['total_new'] > 0:
            logger.info("\n📈 New articles by VC:")
            for vc_name, count in stats['by_vc'].items():
                if count > 0:
                    logger.info(f"  • {vc_name}: {count} new articles")
        else:
            logger.info("\n✅ No new articles found - all VCs up to date")
        
        logger.info("=" * 60)
    
    def get_monitoring_status(self) -> Dict:
        """Get current monitoring status"""
        return {
            'last_run': self.state.get('last_run'),
            'total_articles_tracked': len(self.state['seen_urls']),
            'total_scraped': self.state.get('total_articles_scraped', 0),
            'vc_stats': self.state.get('vc_stats', {}),
            'next_scheduled_run': self.get_next_scheduled_run()
        }
    
    def get_next_scheduled_run(self) -> str:
        """Get next scheduled run time"""
        # This would depend on your scheduling setup
        if self.state.get('last_run'):
            last_run = datetime.fromisoformat(self.state['last_run'])
            next_run = last_run + timedelta(days=1)
            return next_run.strftime('%Y-%m-%d %H:%M:%S')
        return "Not scheduled"
    
    def cleanup_old_entries(self, days_to_keep: int = 90):
        """Clean up old entries from state to prevent it from growing too large"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        cutoff_iso = cutoff_date.isoformat()
        
        original_count = len(self.state['seen_urls'])
        
        # Remove old entries
        self.state['seen_urls'] = {
            url: data for url, data in self.state['seen_urls'].items()
            if data.get('scraped_at', '') >= cutoff_iso
        }
        
        cleaned_count = original_count - len(self.state['seen_urls'])
        if cleaned_count > 0:
            logger.info(f"🧹 Cleaned up {cleaned_count} old entries (kept {days_to_keep} days)")
            self.save_state()


class DailyScheduler:
    def __init__(self, monitor: SmartVCMonitor, run_time: str = "09:00"):
        self.monitor = monitor
        self.run_time = run_time
        
    def start_daily_monitoring(self):
        """Start the daily monitoring schedule"""
        logger.info(f"🕘 Scheduling daily VC monitoring at {self.run_time}")
        
        # Schedule daily run
        schedule.every().day.at(self.run_time).do(self.monitor.run_daily_check)
        
        # Optional: Add a cleanup job weekly
        schedule.every().sunday.at("02:00").do(lambda: self.monitor.cleanup_old_entries())
        
        logger.info("⏰ Scheduler started. Waiting for scheduled runs...")
        logger.info(f"💡 Next run: Today at {self.run_time} (if not already passed)")
        
        # Keep the script running
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute


def main():
    """Main function to run the smart monitoring system"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Smart VC Monitoring System")
    parser.add_argument("--run-now", action="store_true", help="Run check immediately instead of scheduling")
    parser.add_argument("--schedule-time", default="09:00", help="Daily run time (HH:MM format)")
    parser.add_argument("--status", action="store_true", help="Show current monitoring status")
    args = parser.parse_args()
    
    # Initialize monitor
    monitor = SmartVCMonitor()
    
    if args.status:
        # Show status
        status = monitor.get_monitoring_status()
        print("\n📊 MONITORING STATUS")
        print("=" * 40)
        print(f"Last run: {status['last_run'] or 'Never'}")
        print(f"Total articles tracked: {status['total_articles_tracked']}")
        print(f"Total scraped: {status['total_scraped']}")
        print(f"Next scheduled: {status['next_scheduled_run']}")
        print("\n📈 VC Stats:")
        for vc_name, stats in status['vc_stats'].items():
            print(f"  • {vc_name}: {stats.get('total_articles', 0)} articles")
        return
    
    if args.run_now:
        # Run immediately
        logger.info("🏃 Running immediate check...")
        stats = monitor.run_daily_check()
        print(f"\n✅ Check complete: {stats['total_new']} new articles found")
    else:
        # Start scheduler
        scheduler = DailyScheduler(monitor, args.schedule_time)
        scheduler.start_daily_monitoring()


if __name__ == "__main__":
    main()