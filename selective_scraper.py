from multi_vc_scraper import MultiVCScraper
from vc_config import VC_CONFIGS
import argparse

def main():
    parser = argparse.ArgumentParser(description='Scrape specific VCs')
    parser.add_argument('--vcs', nargs='+', choices=list(VC_CONFIGS.keys()), 
                       help='List of VCs to scrape')
    parser.add_argument('--max-articles', type=int, default=30, 
                       help='Maximum articles per VC')
    parser.add_argument('--output', default='output/selected_vc_theses.csv', 
                       help='Output CSV file')
    
    args = parser.parse_args()
    
    scraper = MultiVCScraper()
    
    if args.vcs:
        print(f"Scraping VCs: {', '.join(args.vcs)}")
        articles = scraper.scrape_all_vcs(vc_list=args.vcs, max_articles_per_vc=args.max_articles)
    else:
        print("Scraping all VCs")
        articles = scraper.scrape_all_vcs(max_articles_per_vc=args.max_articles)
    
    scraper.save_to_csv(articles, args.output)
    
    print(f"Completed! Scraped {len(articles)} articles and saved to {args.output}")

if __name__ == "__main__":
    main()
