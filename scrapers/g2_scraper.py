import time
import random
from datetime import datetime
from .base_scraper import BaseScraper
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class G2Scraper(BaseScraper):
    """Scraper for G2.com, built to handle manual CAPTCHA solving."""
    
    def _handle_cookies(self, driver):
        try:
            cookie_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
            )
            cookie_button.click()
            print("Accepted cookies.")
            time.sleep(random.uniform(1.0, 2.0))
        except TimeoutException:
            print("No cookie banner found.")

    def scrape(self):
        driver = self._get_driver()
        all_reviews = []
        try:
            product_slug = self.company_name.lower().replace(' ', '-')
            url = f"https://www.g2.com/products/{product_slug}/reviews"
            driver.get(url)
            
            self._handle_cookies(driver)

            # Wait up to 5 minutes to allow for manual CAPTCHA solving by the user.
            print("\n>>> ACTION REQUIRED: If a CAPTCHA appears, please solve it.")
            print(">>> The script will wait for up to 5 minutes...")
            
            wait = WebDriverWait(driver, 300) 
            
            while True:
                print(f"\nScraping page: {driver.current_url}")
                try:
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.paper:not([class*='advertisement'])")))
                    print("Review container found. Scraping...")
                except TimeoutException:
                    print("Timed out waiting for reviews. Page might be blocked or empty.")
                    break
                
                reviews_on_page = driver.find_elements(By.CSS_SELECTOR, "div.paper:not([class*='advertisement']) div[itemprop='review']")

                for review_div in reviews_on_page:
                    try:
                        title = review_div.find_element(By.CSS_SELECTOR, "h3[itemprop='name']").text.strip()
                        date_str = review_div.find_element(By.CSS_SELECTOR, "div.x-current-review-date").text.strip()
                        review_date = self._parse_date(date_str)
                        
                        if not review_date: continue
                        if review_date < self.start_date:
                            return all_reviews

                        if self.start_date <= review_date <= self.end_date:
                            review_body = review_div.find_element(By.CSS_SELECTOR, "div[itemprop='reviewBody']")
                            try:
                                show_more = review_body.find_element(By.CSS_SELECTOR, "a.js-show-full-review-text")
                                driver.execute_script("arguments[0].click();", show_more)
                                time.sleep(random.uniform(0.5, 1.0))
                            except NoSuchElementException: pass
                            
                            review_text = review_body.text.strip().replace("... Show More", "")
                            rating = f"{review_div.find_element(By.CSS_SELECTOR, 'span.g2-crowd-score__value').text}/5"

                            all_reviews.append({
                                'source': 'G2', 'title': title, 'review': review_text,
                                'date': review_date.strftime("%Y-%m-%d"), 'rating': rating
                            })
                    except Exception:
                        continue
                
                try:
                    next_button = driver.find_element(By.CSS_SELECTOR, "a[aria-label='Next page']")
                    driver.execute_script("arguments[0].click();", next_button)
                    time.sleep(random.uniform(3.5, 5.5))
                except NoSuchElementException:
                    print("No more pages found.")
                    break
        finally:
            driver.quit()
        return all_reviews

    def _parse_date(self, date_str: str) -> datetime:
        clean_date_str = date_str.replace("Reviewed on ", "")
        try:
            return datetime.strptime(clean_date_str, "%B %d, %Y")
        except ValueError:
            return None