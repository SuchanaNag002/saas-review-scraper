import argparse
import json
from datetime import datetime
import sys
from scrapers.g2_scraper import G2Scraper

SOURCE_MAP = {
    "g2": G2Scraper,
}

def main():
    # This part of the code remains the same
    parser = argparse.ArgumentParser(description="Scrape SaaS product reviews using Selenium.")
    parser.add_argument("--company", type=str, required=True, help="Company name to scrape.")
    parser.add_argument("--start-date", type=str, required=True, help="Start date (YYYY-MM-DD).")
    parser.add_argument("--end-date", type=str, required=True, help="End date (YYYY-MM-DD).")
    parser.add_argument("--source", type=str, required=True, choices=["g2"], help="Source: g2.")
    parser.add_argument("--output-file", type=str, default="reviews.json", help="Output JSON file name.")
    parser.add_argument("--headless", action='store_true', help="Run browser in headless mode.")

    args = parser.parse_args()

    try:
        start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
        end_date = datetime.strptime(args.end_date, "%Y-%m-%d")
    except ValueError:
        print("Error: Dates must be in YYYY-MM-DD format.", file=sys.stderr)
        sys.exit(1)

    if start_date > end_date:
        print("Error: Start date cannot be after the end date.", file=sys.stderr)
        sys.exit(1)

    print(f"Initializing scraper for source: {args.source}")
    scraper_class = SOURCE_MAP[args.source]
    scraper = scraper_class(
        company_name=args.company,
        start_date=start_date,
        end_date=end_date,
        is_headless=args.headless
    )

    try:
        print(f"Scraping reviews for '{args.company}' from {start_date.date()} to {end_date.date()}...")
        reviews = scraper.scrape()

        if not reviews:
            print("No reviews found for the specified criteria.")
            return

        with open(args.output_file, 'w', encoding='utf-8') as f:
            json.dump(reviews, f, indent=4, ensure_ascii=False)
        
        print(f"\nSuccessfully scraped {len(reviews)} reviews.")
        print(f"Output saved to {args.output_file}")

    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()