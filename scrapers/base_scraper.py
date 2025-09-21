import os
import json
import time
import re
from datetime import datetime
from typing import List, Dict, Optional, Any
import requests
from abc import ABC, abstractmethod


class BaseScraper(ABC):
    """Base class for all review scrapers"""
    
    def __init__(self, api_token: Optional[str] = None):
        self.api_token = api_token or os.getenv('CRAWLBASE_TOKEN')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def save_to_json(self, data: Dict[str, Any], company_name: str) -> Dict[str, str]:
        """Save scraped data to JSON file"""
        output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'output')
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # Clean product name
        clean_name = re.sub(r' Reviews?$', '', company_name, flags=re.IGNORECASE)
        sanitized_name = re.sub(r'[^a-z0-9]', '_', clean_name.lower())
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        filename = f"{sanitized_name}_{timestamp}.json"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        return {'file_path': filepath, 'filename': filename}
    
    def parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string into datetime object"""
        if not date_str:
            return None
            
        date_str = date_str.strip()
        
        # Try different date formats
        formats = [
            '%Y/%m/%d',
            '%m/%d/%Y',
            '%Y-%m-%d',
            '%m-%d-%Y',
            '%B %d, %Y',
            '%b %d, %Y'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
                
        # Handle relative dates
        return self._parse_relative_date(date_str)
    
    def _parse_relative_date(self, date_str: str) -> Optional[datetime]:
        """Parse relative date strings like '2 months ago'"""
        current_date = datetime.now()
        lower_str = date_str.lower()
        
        if 'year' in lower_str:
            match = re.search(r'(\d+)', date_str)
            if match:
                years = int(match.group(1))
                return datetime(current_date.year - years, current_date.month, current_date.day)
        elif 'month' in lower_str:
            match = re.search(r'(\d+)', date_str)
            if match:
                months = int(match.group(1))
                new_month = current_date.month - months
                new_year = current_date.year
                while new_month <= 0:
                    new_month += 12
                    new_year -= 1
                return datetime(new_year, new_month, current_date.day)
        elif 'day' in lower_str:
            match = re.search(r'(\d+)', date_str)
            if match:
                days = int(match.group(1))
                from datetime import timedelta
                return current_date - timedelta(days=days)
                
        return None
    
    def filter_reviews_by_date(self, reviews: List[Dict], start_date: str, end_date: str) -> List[Dict]:
        """Filter reviews by date range"""
        start_dt = self.parse_date(start_date)
        end_dt = self.parse_date(end_date)
        
        if not start_dt or not end_dt:
            return reviews
            
        filtered_reviews = []
        for review in reviews:
            review_date = self.parse_date(review.get('date', ''))
            if review_date and start_dt <= review_date <= end_dt:
                filtered_reviews.append(review)
                
        return filtered_reviews
    
    def make_request(self, url: str, max_retries: int = 5) -> Optional[str]:
        """Make HTTP request with retries"""
        if self.api_token:
            # Use Crawlbase API
            api_url = f"https://api.crawlbase.com/?token={self.api_token}&url={url}"
            response = requests.get(api_url)
        else:
            # Direct request
            for attempt in range(max_retries):
                try:
                    response = self.session.get(url, timeout=30)
                    if response.status_code == 200:
                        return response.text
                    time.sleep(5)
                except Exception as e:
                    print(f"Request attempt {attempt + 1} failed: {e}")
                    time.sleep(5)
            return None
            
        return response.text if response.status_code == 200 else None
    
    @abstractmethod
    def scrape_reviews(self, company_name: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """Abstract method to scrape reviews"""
        pass
    
    @abstractmethod
    def parse_review_page(self, html: str) -> Dict[str, Any]:
        """Abstract method to parse review page HTML"""
        pass