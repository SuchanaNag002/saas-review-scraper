import os
import sys
import argparse
import json
from datetime import datetime
from dotenv import load_dotenv

from scrapers import G2Scraper, CapterraScraper

# Load environment variables
load_dotenv()


def validate_date(date_string: str) -> str:
    """Validate date format"""
    try:
        datetime.strptime(date_string, '%Y-%m-%d')
        return date_string
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid date format: {date_string}. Use YYYY-MM-DD")


def validate_date_range(start_date: str, end_date: str) -> bool:
    """Validate that start date is before end date"""
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    return start <= end


def get_scraper(source: str):
    """Get appropriate scraper based on source"""
    scrapers = {
        'g2': G2Scraper,
        'capterra': CapterraScraper
    }
    return scrapers.get(source.lower())


def main():
    parser = argparse.ArgumentParser(
        description='Scrape product reviews from G2 and Capterra',
        epilog='''
Examples:
  python main.py --company "Slack" --start-date "2024-01-01" --end-date "2024-12-31" --source "g2"
  python main.py --company "Zoom" --start-date "2024-06-01" --end-date "2024-12-31" --source "capterra"
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--company',
        required=True,
        help='Company name to scrape reviews for'
    )
    
    parser.add_argument(
        '--start-date',
        required=True,
        type=validate_date,
        help='Start date for reviews (YYYY-MM-DD format)'
    )
    
    parser.add_argument(
        '--end-date',
        required=True,
        type=validate_date,
        help='End date for reviews (YYYY-MM-DD format)'
    )
    
    parser.add_argument(
        '--source',
        required=True,
        choices=['g2', 'capterra'],
        help='Source to scrape reviews from'
    )
    
    parser.add_argument(
        '--output-dir',
        default='output',
        help='Output directory for JSON files (default: output)'
    )
    
    parser.add_argument(
        '--api-token',
        help='Crawlbase API token (can also be set via CRAWLBASE_TOKEN env variable)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    # Validate date range
    if not validate_date_range(args.start_date, args.end_date):
        print("Error: Start date must be before or equal to end date")
        sys.exit(1)
    
    # Create output directory if it doesn't exist
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
    
    # Get API token from args or environment
    api_token = args.api_token or os.getenv('CRAWLBASE_TOKEN')
    
    if args.verbose:
        print(f"Company: {args.company}")
        print(f"Date range: {args.start_date} to {args.end_date}")
        print(f"Source: {args.source}")
        print(f"Output directory: {args.output_dir}")
        print(f"API token configured: {'Yes' if api_token else 'No'}")
        print("-" * 50)
    
    try:
        # Get appropriate scraper
        scraper_class = get_scraper(args.source)
        if not scraper_class:
            print(f"Error: Unsupported source '{args.source}'")
            sys.exit(1)
        
        # Initialize scraper
        scraper = scraper_class(api_token=api_token)
        
        # Start scraping
        print(f"Starting to scrape {args.source.upper()} reviews for '{args.company}'...")
        
        result = scraper.scrape_reviews(
            company_name=args.company,
            start_date=args.start_date,
            end_date=args.end_date
        )
        
        if 'error' in result:
            print(f"Error during scraping: {result['error']}")
            sys.exit(1)
        
        # Save results
        file_info = scraper.save_to_json(result, args.company)
        
        # Print summary
        print("\n" + "="*50)
        print("SCRAPING COMPLETE")
        print("="*50)
        print(f"Company: {result.get('product_name', args.company)}")
        print(f"Source: {args.source.upper()}")
        print(f"Overall Rating: {result.get('stars', 'N/A')}")
        print(f"Total Reviews (from website): {result.get('total_reviews', 'N/A')}")
        print(f"Reviews Scraped (after date filtering): {result.get('total_scraped_reviews', 0)}")
        print(f"Date Range: {args.start_date} to {args.end_date}")
        print(f"Output File: {file_info['file_path']}")
        print("="*50)
        
        # Show sample review if available
        if result.get('all_reviews') and args.verbose:
            print("\nSample Review:")
            sample = result['all_reviews'][0]
            print(f"Reviewer: {sample.get('reviewer_name', 'N/A')}")
            print(f"Rating: {sample.get('rating', 'N/A')}")
            print(f"Date: {sample.get('date', 'N/A')}")
            print(f"Title: {sample.get('title', 'N/A')}")
            description = sample.get('description', '')
            if description:
                print(f"Description: {description[:200]}{'...' if len(description) > 200 else ''}")
        
    except KeyboardInterrupt:
        print("\nScraping interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()