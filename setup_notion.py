import os
from notion_client import Client
import logging
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Now you can access the variables using os.getenv()
notion_token = os.getenv('NOTION_TOKEN')
database_id = os.getenv('NOTION_DATABASE_ID')

def get_notion_credentials():
    """Get Notion credentials from user"""
    print("\n📋 Step 1: Get your Notion Integration Token")
    print("1. Go to https://www.notion.so/my-integrations or https://developers.notion.com/")
    print("2. Select or create your integration (e.g., 'VC Scraper').")
    print("3. Navigate to the 'Secrets' or 'Configuration' tab for your integration.")
    print("4. Copy the 'Internal Integration Secret' or 'Internal Integration Token'.")
    print("   It's a long string of characters (e.g., starting with 'ntn_' or 'secret_').")
    
    token = input("\nEnter your Notion Integration Token/Secret: ").strip()
    
    # Basic validation for token length, as prefixes can vary.
    # Notion tokens are typically quite long.
    if len(token) < 40:
        print("❌ The token seems too short. Please ensure you've copied the entire string.")
        print("   It should be a long string of characters provided by Notion.")
        return None, None
    
    print("\n✅ Token format looks plausible.")
    print("\n📋 Step 2: Get your Notion Page ID")
    print("1. Open Notion in your browser")
    print("2. Create or navigate to a page where you want the database")
    print("3. Copy the URL - it looks like: https://www.notion.so/Page-Name-32chars")
    print("4. The page ID is the 32-character string at the end")
    
    page_id = input("\nEnter your Notion Page ID: ").strip()
    
    # Clean up page ID (remove dashes if present)
    page_id = page_id.replace('-', '')
    
    if len(page_id) != 32:
        print("❌ Invalid page ID length. Should be 32 characters (after removing any hyphens).")
        return None, None
    
    return token, page_id

def create_notion_database(token, page_id):
    """Create the Notion database with proper schema"""
    
    notion = Client(auth=token)
    
    # Database schema
    database_properties = {
        "Title": {"title": {}},
        "VC Firm": {
            "select": {
                "options": [
                    {"name": "Accel India", "color": "blue"},
                    {"name": "Peak XV Partners (formerly Sequoia Capital India)", "color": "red"},
                    {"name": "Kalaari Capital", "color": "green"},
                    {"name": "Matrix Partners India (Z47)", "color": "yellow"},
                    {"name": "Nexus Venture Partners", "color": "orange"},
                    {"name": "Blume Ventures", "color": "purple"},
                    {"name": "Chiratae Ventures", "color": "pink"},
                    {"name": "ah! Ventures", "color": "brown"}
                ]
            }
        },
        "URL": {"url": {}},
        "Date": {"date": {}},
        "Content Hash": {"rich_text": {}},
        "Status": {
            "select": {
                "options": [
                    {"name": "New", "color": "green"},
                    {"name": "Reviewed", "color": "yellow"},
                    {"name": "Archived", "color": "gray"}
                ]
            }
        },
        "Investment Theme": {
            "multi_select": {
                "options": [
                    {"name": "AI/ML", "color": "blue"},
                    {"name": "Fintech", "color": "green"},
                    {"name": "Healthcare", "color": "red"},
                    {"name": "SaaS", "color": "purple"},
                    {"name": "E-commerce", "color": "orange"},
                    {"name": "EdTech", "color": "yellow"},
                    {"name": "Gaming", "color": "pink"},
                    {"name": "Mobility", "color": "brown"},
                    {"name": "Crypto/Web3", "color": "default"},
                    {"name": "Developer Tools", "color": "gray"},
                    {"name": "General", "color": "default"}
                ]
            }
        },
        "Company": {"rich_text": {}},
        "Source": {
            "select": {
                "options": [
                    {"name": "Auto-Scraped", "color": "blue"},
                    {"name": "Manual", "color": "green"}
                ]
            }
        }
    }
    
    try:
        # Create database
        database = notion.databases.create(
            parent={"type": "page_id", "page_id": page_id},
            title=[{"type": "text", "text": {"content": "VC Articles Database"}}],
            properties=database_properties
        )
        
        database_id = database['id']
        print(f"\n✅ Database created successfully!")
        print(f"📊 Database ID: {database_id}")
        print(f"🔗 Database URL: {database['url']}")
        
        # Save to .env file
        env_content = f"""# Notion Integration
NOTION_TOKEN={token}
NOTION_DATABASE_ID={database_id}

# Optional: Webhook for real-time updates
WEBHOOK_URL=https://your-webhook-url.com/trigger-scan

# Optional: Slack notifications
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/your/slack/webhook
"""
        
        with open('.env', 'w') as f:
            f.write(env_content)
        
        print(f"\n💾 Credentials saved to .env file")
        print(f"\n🔧 Next steps:")
        print(f"1. Share the database with your integration:")
        print(f"   - Open the database in Notion")
        print(f"   - Click 'Share' → 'Invite' → Select your integration")
        print(f"2. Test the connection by running: python test_notion.py")
        
        return database_id
        
    except Exception as e:
        logger.error(f"Error creating database: {e}")
        print(f"\n❌ Error creating database: {e}")
        
        if "unauthorized" in str(e).lower() or "Invalid token" in str(e): # Added "Invalid token" check
            print("\n💡 This 'unauthorized' or 'invalid token' error usually means:")
            print("1. The Integration Token/Secret in your .env file is incorrect or has a typo.")
            print("2. The Notion database has NOT been shared with your specific integration.")
            print("   Go to your Notion Page/Database -> Share -> Invite -> Select your integration.")
            print("3. The Page ID used to create the database is incorrect or the integration doesn't have access to it.")
        
        return None

def test_connection(token, database_id):
    """Test the Notion connection"""
    try:
        notion = Client(auth=token)
        database = notion.databases.retrieve(database_id=database_id)
        print(f"✅ Successfully connected to database: {database.get('title', [{}])[0].get('text', {}).get('content', 'Untitled Database')}")
        return True
    except Exception as e:
        print(f"❌ Error connecting to Notion: {e}")
        if "unauthorized" in str(e).lower() or "Invalid token" in str(e): # Added "Invalid token" check
            print("\n💡 This 'unauthorized' or 'invalid token' error usually means:")
            print("1. The Integration Token/Secret in your .env file is incorrect or has a typo.")
            print("2. The Notion database has NOT been shared with your specific integration.")
            print("   Go to your Notion Page/Database -> Share -> Invite -> Select your integration.")
        return False

def main():
    print("🚀 Notion Database Setup for VC Scraper")
    print("="*50)
    
    # Check if .env file exists
    if os.path.exists('.env'):
        choice = input("\n.env file found. Do you want to:\n1. Create new database\n2. Test existing connection\nChoose (1/2): ")
    else:
        choice = "1"
        print("\nNo .env file found. Creating new database...")
    
    if choice == "1":
        token, page_id = get_notion_credentials()
        if token and page_id:
            database_id = create_notion_database(token, page_id)
            if database_id:
                print("\n🎉 Setup complete! You can now run the scraper with Notion integration.")
    
    elif choice == "2":
        from dotenv import load_dotenv
        load_dotenv()
        token = os.getenv('NOTION_TOKEN')
        database_id = os.getenv('NOTION_DATABASE_ID')
        if not token or not database_id:
            print("❌ Missing credentials in .env file")
        else:
            test_connection(token, database_id)
    
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main()

