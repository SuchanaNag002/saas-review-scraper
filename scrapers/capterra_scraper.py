from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup
from .base_scraper import BaseScraper


class CapterraScraper(BaseScraper):
    """Scraper for Capterra reviews"""
    
    def scrape_reviews(self, company_name: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """Scrape reviews from Capterra for a specific company and date range"""
        base_url = f"https://www.capterra.com/p/{company_name.lower().replace(' ', '-')}"
        
        print(f"Starting to scrape {base_url} (Capterra)")
        
        try:
            html = self.make_request(base_url)
            if not html:
                return {'error': 'Failed to fetch page'}
                
            parsed_result = self.parse_review_page(html)
            
            if 'error' in parsed_result:
                return parsed_result
            
            product_data = parsed_result['product_data']
            
            # Clean product name
            clean_name = product_data['product_name'].replace(' Reviews', '')
            product_info = {
                'product_name': clean_name,
                'stars': product_data['stars'],
                'total_reviews': product_data['total_reviews']
            }
            
            # Filter reviews by date range
            all_reviews = product_data['all_reviews']
            filtered_reviews = self._filter_reviews_by_date_range(all_reviews, start_date, end_date)
            
            return {
                **product_info,
                'all_reviews': filtered_reviews,
                'total_scraped_reviews': len(filtered_reviews)
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def parse_review_page(self, html: str) -> Dict[str, Any]:
        """Parse Capterra review page HTML"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            product_data = {
                'product_name': '',
                'stars': '',
                'total_reviews': '',
                'all_reviews': []
            }
            
            # Extract product name
            product_name_elem = soup.select_one('div#productHeader > div.container > div#productHeaderInfo > div.col > h1.mb-1')
            if product_name_elem:
                product_data['product_name'] = product_name_elem.get_text(strip=True)
            
            # Extract stars
            stars_elem = soup.select_one('div#productHeader > div.container > div#productHeaderInfo > div.col > div.align-items-center.d-flex > span.star-rating-component > span.d-flex > span.ms-1')
            if stars_elem:
                product_data['stars'] = stars_elem.get_text(strip=True)
            
            # Extract reviews
            review_elements = soup.select('#reviews > div.review-card, div.i18n-translation_container.review-card')
            
            for element in review_elements:
                # Reviewer name
                reviewer_name_elem = element.select_one('div.ps-0 > div.fw-bold, div.col > div.h5.fw-bold')
                reviewer_name = reviewer_name_elem.get_text(strip=True) if reviewer_name_elem else ''
                
                # Profile title
                profile_title_elem = element.select_one('div.ps-0 > div.text-ash, div.col > div.text-ash')
                profile_title = profile_title_elem.get_text(strip=True) if profile_title_elem else ''
                
                # Stars
                stars_elem = element.select_one('div.text-ash > span.ms-1, span.star-rating-component span.ms-1')
                stars = stars_elem.get_text(strip=True) if stars_elem else ''
                
                # Review date
                date_elem = element.select_one('div.text-ash > span.ms-2, span.ms-2')
                review_date = date_elem.get_text(strip=True) if date_elem else ''
                
                # Review text (Comments section)
                comment_section = element.select_one("p span:contains('Comments:')")
                review_text = ''
                if comment_section:
                    parent = comment_section.parent
                    spans = parent.select('span')
                    for span in spans:
                        if 'Comments:' not in span.get_text():
                            review_text += span.get_text(strip=True) + ' '
                
                # Pros
                pros_section = element.select_one("p:contains('Pros:')")
                pros = ''
                if pros_section and pros_section.next_sibling:
                    pros = pros_section.next_sibling.get_text(strip=True) if hasattr(pros_section.next_sibling, 'get_text') else ''
                
                # Cons
                cons_section = element.select_one("p:contains('Cons:')")
                cons = ''
                if cons_section and cons_section.next_sibling:
                    cons = cons_section.next_sibling.get_text(strip=True) if hasattr(cons_section.next_sibling, 'get_text') else ''
                
                review_data = {
                    'reviewer_name': reviewer_name,
                    'title': '',  # Capterra doesn't have separate review titles
                    'description': review_text.strip(),
                    'rating': stars,
                    'date': review_date,
                    'profile_title': profile_title,
                    'pros': pros,
                    'cons': cons
                }
                
                product_data['all_reviews'].append(review_data)
            
            product_data['total_reviews'] = str(len(product_data['all_reviews']))
            
            return {'product_data': product_data}
            
        except Exception as e:
            return {'error': str(e)}
    
    def _filter_reviews_by_date_range(self, reviews: List[Dict], start_date: str, end_date: str) -> List[Dict]:
        """Filter reviews by date range using relative date parsing"""
        filtered_reviews = []
        
        for review in reviews:
            if self._is_review_in_date_range(review['date'], start_date, end_date):
                filtered_reviews.append(review)
        
        return filtered_reviews
    
    def _is_review_in_date_range(self, review_date_str: str, start_date: str, end_date: str) -> bool:
        """Check if review date falls within the specified range"""
        review_date = self._calculate_date_from_relative(review_date_str)
        start_dt = self.parse_date(start_date)
        end_dt = self.parse_date(end_date)
        
        if not review_date or not start_dt or not end_dt:
            return False
            
        return start_dt <= review_date <= end_dt
    
    def _calculate_date_from_relative(self, relative_time_str: str) -> Optional[Any]:
        """Calculate actual date from relative time string"""
        return self._parse_relative_date(relative_time_str)