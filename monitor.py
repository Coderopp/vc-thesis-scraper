#!/usr/bin/env python3
"""
Smart VC Monitor Runner
A simple script to run the intelligent VC monitoring system
"""

import sys
import os
import argparse
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.smart_monitor import SmartVCMonitor, DailyScheduler

def main():
    parser = argparse.ArgumentParser(
        description="Smart VC Article Monitoring System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python monitor.py --run-now                    # Run check immediately
  python monitor.py --schedule                   # Start daily scheduler (9 AM)
  python monitor.py --schedule --time 14:30      # Schedule for 2:30 PM daily
  python monitor.py --status                     # Show monitoring status
        """
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--run-now", action="store_true", 
                      help="Run check immediately and exit")
    group.add_argument("--schedule", action="store_true", 
                      help="Start daily scheduler (keeps running)")
    group.add_argument("--status", action="store_true", 
                      help="Show current monitoring status")
    
    parser.add_argument("--time", default="09:00", 
                       help="Daily run time in HH:MM format (default: 09:00)")
    parser.add_argument("--csv-file", 
                       default="output/vc_articles_incremental.csv",
                       help="CSV file for incremental saves")
    parser.add_argument("--state-file", 
                       default="data/scraper_state.json",
                       help="State file to track processed articles")
    
    args = parser.parse_args()
    
    # Validate time format
    try:
        datetime.strptime(args.time, "%H:%M")
    except ValueError:
        print("❌ Invalid time format. Use HH:MM (e.g., 09:00, 14:30)")
        return 1
    
    # Initialize monitor with custom files if specified
    monitor = SmartVCMonitor(
        state_file=args.state_file,
        csv_file=args.csv_file
    )
    
    if args.status:
        show_status(monitor)
        return 0
    
    if args.run_now:
        run_immediate_check(monitor)
        return 0
    
    if args.schedule:
        start_scheduler(monitor, args.time)
        return 0

def show_status(monitor: SmartVCMonitor):
    """Show detailed monitoring status"""
    status = monitor.get_monitoring_status()
    
    print("\n" + "="*60)
    print("📊 SMART VC MONITORING STATUS")
    print("="*60)
    print(f"📅 Last run: {status['last_run'] or 'Never'}")
    print(f"📰 Total articles tracked: {status['total_articles_tracked']}")
    print(f"📈 Total articles scraped: {status['total_scraped']}")
    print(f"⏰ Next scheduled run: {status['next_scheduled_run']}")
    
    if status['vc_stats']:
        print(f"\n📊 VC STATISTICS:")
        print("-" * 40)
        for vc_name, stats in status['vc_stats'].items():
            last_scraped = stats.get('last_scraped', 'Never')
            if last_scraped != 'Never':
                last_scraped = datetime.fromisoformat(last_scraped).strftime('%Y-%m-%d %H:%M')
            print(f"• {vc_name}")
            print(f"  Articles: {stats.get('total_articles', 0)}")
            print(f"  Last check: {last_scraped}")
    else:
        print("\n📊 No VC statistics available yet")
    
    print("="*60)

def run_immediate_check(monitor: SmartVCMonitor):
    """Run an immediate check for new articles"""
    print("\n🚀 Running immediate check for new VC articles...")
    print("⏱️  This will only process articles that haven't been seen before")
    
    try:
        stats = monitor.run_daily_check()
        
        print("\n" + "="*60)
        print("✅ IMMEDIATE CHECK COMPLETE")
        print("="*60)
        print(f"🕐 Runtime: {stats['runtime_minutes']} minutes")
        print(f"📰 New articles found: {stats['total_new']}")
        print(f"❌ Errors: {stats['errors']}")
        
        if stats['total_new'] > 0:
            print(f"\n📈 New articles by VC:")
            for vc_name, count in stats['by_vc'].items():
                if count > 0:
                    print(f"  • {vc_name}: {count} new articles")
            print(f"\n💾 New articles saved to CSV and Notion (if configured)")
        else:
            print(f"\n✅ All VCs are up to date - no new articles found")
        
        print("="*60)
        
    except KeyboardInterrupt:
        print("\n⏹️  Check interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during check: {e}")

def start_scheduler(monitor: SmartVCMonitor, run_time: str):
    """Start the daily scheduler"""
    print("\n🕘 STARTING DAILY VC MONITORING SCHEDULER")
    print("="*60)
    print(f"⏰ Scheduled time: {run_time} daily")
    print(f"📁 State file: {monitor.state_file}")
    print(f"📊 CSV output: {monitor.csv_file}")
    print(f"💾 Notion integration: {'✅ Enabled' if monitor.notion_token else '❌ Disabled'}")
    print("\n💡 The scheduler will:")
    print("   • Check for new articles daily")
    print("   • Only process articles not seen before")
    print("   • Save new articles to CSV and Notion")
    print("   • Clean up old state data weekly")
    print("\n⚠️  Press Ctrl+C to stop the scheduler")
    print("="*60)
    
    try:
        scheduler = DailyScheduler(monitor, run_time)
        scheduler.start_daily_monitoring()
    except KeyboardInterrupt:
        print("\n⏹️  Scheduler stopped by user")
        print("👋 Goodbye!")

if __name__ == "__main__":
    sys.exit(main())