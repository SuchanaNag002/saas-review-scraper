import json
import argparse
from datetime import datetime
from scrapers.capterra_scraper import CapterraScraper

def main():
    parser = argparse.ArgumentParser(description='Scrape Capterra reviews')
    parser.add_argument('--company', required=True, help='Company name')
    parser.add_argument('--start-date', required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', required=True, help='End date (YYYY-MM-DD)')
    parser.add_argument('--headless', action='store_true', help='Run headless')
    parser.add_argument('--output', help='Output JSON file')
    
    args = parser.parse_args()
    
    try:
        start_dt = datetime.strptime(args.start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(args.end_date, "%Y-%m-%d")
        
        if start_dt > end_dt:
            print("Error: Start date must be before end date")
            return 1
        
        print(f"Scraping Capterra reviews for '{args.company}'")
        print(f"Date range: {args.start_date} to {args.end_date}")
        
        scraper = CapterraScraper(args.company, start_dt, end_dt, args.headless)
        reviews = scraper.scrape()
        
        output_data = {
            'company': args.company,
            'source': 'Capterra',
            'date_range': {
                'start': args.start_date,
                'end': args.end_date
            },
            'scrape_timestamp': datetime.now().isoformat(),
            'total_reviews': len(reviews),
            'reviews': reviews
        }
        
        if args.output:
            output_file = args.output
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"{args.company.replace(' ', '_')}_capterra_reviews_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"\nCompleted! Found {len(reviews)} reviews")
        print(f"Output saved to: {output_file}")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())