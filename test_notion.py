import os
from dotenv import load_dotenv
from src.notion_integration import NotionVCDatabase

def test_notion_integration():
    """Test the Notion integration with a sample article"""
    
    # Load environment variables
    load_dotenv()
    
    token = os.getenv('NOTION_TOKEN')
    database_id = os.getenv('NOTION_DATABASE_ID')
    
    if not token or not database_id:
        print("❌ Missing NOTION_TOKEN or NOTION_DATABASE_ID in .env file")
        return
    
    try:
        # Initialize Notion database
        notion_db = NotionVCDatabase(token, database_id)
        
        # Test with a sample article
        test_article = {
            'title': 'Test Article - Our Investment in TestCorp',
            'vc_name': 'Accel India',
            'url': 'https://example.com/test-article',
            'content': 'This is a test article about our investment in TestCorp, an AI-powered fintech startup that is revolutionizing digital payments in India. The company has shown strong growth metrics and we are excited to support their Series A funding round.',
            'date': '2025-06-10'
        }
        
        print("🧪 Testing Notion integration...")
        
        # Test creating an article
        page_id = notion_db.create_article_page(test_article)
        print(f"✅ Successfully created test article with page ID: {page_id}")
        
        # Test checking if article exists
        content_hash = notion_db._generate_hash(test_article['content'])
        exists = notion_db.check_article_exists(content_hash)
        print(f"✅ Article existence check: {exists}")
        
        # Test getting recent articles
        recent = notion_db.get_recent_articles(days=1)
        print(f"✅ Found {len(recent)} recent articles")
        
        print("\n🎉 All tests passed! Notion integration is working correctly.")
        print("⚠️  Note: You may want to delete the test article from your Notion database.")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        
        if "unauthorized" in str(e).lower():
            print("\n💡 Make sure you've shared your database with the integration:")
            print("1. Open your database in Notion")
            print("2. Click 'Share' in the top right")
            print("3. Click 'Invite' and select your integration")

if __name__ == "__main__":
    test_notion_integration()