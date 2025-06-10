import os
import argparse
import pandas as pd
import logging
from dotenv import load_dotenv

# Assuming your scraper and config loader are structured like this:
from src.multi_vc_scraper import EnhancedMultiVCScraper # Or your main scraper class
from config.vc_config import load_vc_configs # Function to load VC sources

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def save_articles_to_csv(articles, filename="output/vc_theses_scraped.csv"):
    if not articles:
        logger.info("No articles to save to CSV.")
        return
    try:
        df = pd.DataFrame(articles)
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        df.to_csv(filename, index=False)
        logger.info(f"Successfully saved {len(articles)} articles to {filename}")
    except Exception as e:
        logger.error(f"Error saving articles to CSV {filename}: {e}")

def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="VC Thesis Scraper")
    parser.add_argument(
        "--no-notion", 
        action="store_true", 
        help="Disable Notion integration and only output to CSV."
    )
    parser.add_argument(
        "--output-csv", 
        default="output/scraped_vc_articles.csv", 
        help="Path to save the output CSV file."
    )
    args = parser.parse_args()

    notion_token = os.getenv('NOTION_TOKEN')
    database_id = os.getenv('NOTION_DATABASE_ID')

    use_notion_integration = True
    if args.no_notion:
        logger.info("Notion integration explicitly disabled via --no-notion flag.")
        use_notion_integration = False
    elif not notion_token or not database_id:
        logger.info("Notion token or database ID not found in .env. Notion integration will be disabled.")
        use_notion_integration = False
    
    scraper_instance = None
    if use_notion_integration:
        logger.info("Notion integration is ENABLED.")
        scraper_instance = EnhancedMultiVCScraper(notion_token=notion_token, database_id=database_id)
    else:
        logger.info("Notion integration is DISABLED. Output will be CSV only.")
        # Initialize without Notion credentials. 
        # The EnhancedMultiVCScraper should handle this by setting self.notion_db to None.
        scraper_instance = EnhancedMultiVCScraper() 

    # --- Load VC Configurations ---
    # This part depends on how your vc_sources.yaml is loaded.
    # Assuming load_vc_configs() returns a list of dictionaries.
    try:
        vc_configurations = load_vc_configs()
        if not vc_configurations:
            logger.error("No VC configurations loaded. Exiting.")
            return
    except Exception as e:
        logger.error(f"Failed to load VC configurations: {e}. Exiting.")
        return

    # --- Scraping ---
    all_scraped_articles = []
    logger.info("Starting scraping process...")
    # The scraper_instance should have a method to iterate through vc_configurations
    # and scrape articles. Let's assume it's `run_full_scrape` or similar,
    # or you loop here and call a method per VC.
    # For simplicity, let's assume a method that takes all configs:
    # This part needs to align with your scraper's actual methods.
    # A common pattern is to loop through configs and call a scrape_one_vc method.
    
    # Example loop (adjust to your scraper's methods):
    for i, vc_conf in enumerate(vc_configurations, 1):
        try:
            logger.info(f"[{i}/{len(vc_configurations)}] Scraping articles from: {vc_conf.get('name', 'Unknown VC')}")
            # Use the correct method signature: scrape_vc(vc_key, vc_config, max_articles)
            vc_key = vc_conf.get('key')
            # Reduced max_articles to 10 for faster testing
            articles_from_vc = scraper_instance.scrape_vc(vc_key, vc_conf, max_articles=10) 
            if articles_from_vc:
                all_scraped_articles.extend(articles_from_vc)
                logger.info(f"✅ Scraped {len(articles_from_vc)} articles from {vc_conf.get('name')}.")
            else:
                logger.info(f"⚠️  No articles found for {vc_conf.get('name')}.")
        except Exception as e:
            logger.error(f"❌ Error scraping {vc_conf.get('name', 'Unknown VC')}: {e}")
        except KeyboardInterrupt:
            logger.info(f"⏹️  Scraping interrupted by user. Saving {len(all_scraped_articles)} articles collected so far...")
            break


    if not all_scraped_articles:
        logger.warning("No articles were scraped in total.")
    else:
        logger.info(f"Total articles scraped: {len(all_scraped_articles)}")
        # Save to CSV
        save_articles_to_csv(all_scraped_articles, args.output_csv)

    # --- Notion Processing (Conditional) ---
    if use_notion_integration and scraper_instance.notion_db and all_scraped_articles:
        logger.info("Processing and storing articles in Notion...")
        # This method should exist in EnhancedMultiVCScraper
        stats = scraper_instance.process_and_store_articles(all_scraped_articles) 
        logger.info(f"Notion sync: {stats.get('new',0)} new, {stats.get('existing',0)} existing, {stats.get('errors',0)} errors.")
    
    logger.info("Scraping process finished.")

if __name__ == "__main__":
    main()