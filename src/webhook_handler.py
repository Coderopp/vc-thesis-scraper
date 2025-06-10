# New file: src/webhook_handler.py
from flask import Flask, request, jsonify
from enhanced_scraper import EnhancedMultiVCScraper
import os

app = Flask(__name__)

@app.route('/trigger-scan', methods=['POST'])
def trigger_scan():
    """Webhook endpoint to trigger immediate scan"""
    try:
        scraper = EnhancedMultiVCScraper(
            notion_token=os.getenv('NOTION_TOKEN'),
            database_id=os.getenv('NOTION_DATABASE_ID')
        )
        
        # Quick scan for very recent articles
        articles = scraper.scrape_all_vcs(max_articles_per_vc=5)
        stats = scraper.process_and_store_articles(articles)
        
        return jsonify({"status": "success", "stats": stats})
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500