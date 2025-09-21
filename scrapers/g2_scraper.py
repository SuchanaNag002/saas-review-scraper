import time
import re
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup
from .base_scraper import BaseScraper


class G2Scraper(BaseScraper):
    """Scraper for G2 reviews"""
    
    def scrape_reviews(self, company_name: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """Scrape reviews from G2 for a specific company and date range"""
        base_url = f"https://www.g2.com/products/{company_name.lower().replace(' ', '-')}/reviews"
        
        current_page = 1
        has_next_page = True
        all_reviews = []
        product_info = {}
        
        print(f"Starting to scrape {base_url} (G2)")
        
        while has_next_page:
            current_url = self._generate_page_url(base_url, current_page)
            print(f"Scraping page {current_page}: {current_url}")
            
            try:
                html = self.make_request(current_url)
                if not html:
                    print(f"Failed to fetch page {current_page}")
                    break
                    
                parsed_result = self.parse_review_page(html)
                
                if 'error' in parsed_result:
                    print(f"Error parsing page {current_page}: {parsed_result['error']}")
                    break
                
                if current_page == 1:
                    product_info = {
                        'product_name': parsed_result['product_data']['product_name'],
                        'stars': parsed_result['product_data']['stars'],
                        'total_reviews': parsed_result['product_data']['total_reviews']
                    }
                
                page_reviews = parsed_result['product_data']['all_reviews']
                all_reviews.extend(page_reviews)
                
                print(f"Found {len(page_reviews)} reviews on page {current_page}")
                
                has_next_page = parsed_result.get('has_next_page', False)
                current_page += 1
                
                # Rate limiting
                time.sleep(25)
                
            except Exception as e:
                print(f"Failed to scrape page {current_page}: {e}")
                break
        
        # Filter reviews by date
        filtered_reviews = self.filter_reviews_by_date(all_reviews, start_date, end_date)
        
        return {
            **product_info,
            'all_reviews': filtered_reviews,
            'total_scraped_reviews': len(filtered_reviews)
        }
    
    def parse_review_page(self, html: str) -> Dict[str, Any]:
        """Parse G2 review page HTML"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            product_data = {
                'product_name': '',
                'stars': '',
                'total_reviews': '',
                'all_reviews': []
            }
            
            # Extract product name
            product_title = soup.select_one('div.product-head__title a.c-midnight-100')
            if product_title:
                product_data['product_name'] = product_title.get_text(strip=True)
            
            # Extract stars
            stars_elem = soup.select_one('#products-dropdown .fw-semibold')
            if stars_elem:
                product_data['stars'] = stars_elem.get_text(strip=True)
            
            # Extract total reviews
            total_reviews_elem = soup.select_one('.filters-product h3')
            if total_reviews_elem:
                product_data['total_reviews'] = total_reviews_elem.get_text(strip=True)
            
            # Check for next page
            pagination = soup.select_one('.pagination')
            has_next_page = pagination and 'Next' in pagination.get_text() if pagination else False
            
            # Extract reviews
            review_elements = soup.select('.nested-ajax-loading > div.paper')
            
            for element in review_elements:
                reviewer_name_elem = element.select_one('[itemprop=author]')
                stars_elem = element.select_one('[itemprop="ratingValue"]')
                review_text_elem = element.select_one('.pjax')
                review_link_elem = element.select_one('.pjax')
                profile_title_elems = element.select('.mt-4th')
                review_date_elem = element.select_one('time')
                
                review_data = {
                    'reviewer_name': reviewer_name_elem.get_text(strip=True) if reviewer_name_elem else '',
                    'title': '',  # G2 doesn't seem to have separate titles
                    'description': re.sub(r'[^a-zA-Z ]', '', review_text_elem.get_text(strip=True)) if review_text_elem else '',
                    'rating': stars_elem.get('content') if stars_elem else '',
                    'date': review_date_elem.get_text(strip=True) if review_date_elem else '',
                    'profile_title': ' '.join([elem.get_text(strip=True) for elem in profile_title_elems]),
                    'review_link': review_link_elem.get('href') if review_link_elem else ''
                }
                
                product_data['all_reviews'].append(review_data)
            
            return {
                'product_data': product_data,
                'has_next_page': has_next_page
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _generate_page_url(self, base_url: str, page_num: int) -> str:
        """Generate URL for specific page number"""
        if page_num == 1:
            return base_url
            
        if '?' in base_url:
            return f"{base_url}&page={page_num}"
        else:
            return f"{base_url}?page={page_num}"