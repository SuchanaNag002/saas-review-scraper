import time
import random
from datetime import datetime
from .base_scraper import BaseScraper
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class CapterraScraper(BaseScraper):
    """Optimized Capterra scraper with smart pagination and date filtering."""

    def scrape(self):
        driver = self._get_driver()
        if not driver:
            return []
            
        all_reviews = []
        try:
            search_url = f"https://www.capterra.com/search?query={self.company_name.replace(' ', '%20')}"
            print(f"Navigating to: {search_url}")
            
            # Navigate with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    driver.get(search_url)
                    # Wait for page to start loading
                    time.sleep(5)
                    # Stop loading after basic elements are there
                    driver.execute_script("window.stop();")
                    print(f"Page loaded (attempt {attempt + 1})")
                    break
                except Exception as e:
                    if attempt < max_retries - 1:
                        print(f"Navigation attempt {attempt + 1} failed, retrying...")
                        time.sleep(3)
                    else:
                        raise e

            print("\n>>> ACTION REQUIRED: Please solve any CAPTCHA on the search page.")
            print(">>> Then click on the correct product from search results.")
            print(">>> Finally, click 'View all reviews' or 'Reviews' link.")
            print(f">>> Current URL: {driver.current_url}")
            print(">>> Waiting up to 5 minutes for you to navigate to reviews page...")
            
            try:
                WebDriverWait(driver, 300).until(EC.url_contains("/reviews"))
                print(f"Reviews page loaded: {driver.current_url}")
            except TimeoutException:
                print(f"Timeout: Failed to navigate to a reviews page for '{self.company_name}'.")
                print(f"Current URL: {driver.current_url}")
                return []

            # Simple sorting attempt - just try the basic approach once
            try:
                print("Attempting to sort by 'Most Recent'...")
                sort_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Sort by)]"))
                )
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", sort_button)
                time.sleep(1)
                driver.execute_script("arguments[0].click();", sort_button)

                most_recent_option = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//label[contains(., 'Most Recent')]"))
                )
                driver.execute_script("arguments[0].click();", most_recent_option)
                print("Successfully sorted by 'Most Recent'")
                time.sleep(5)
            except Exception:
                print("Sorting failed. Proceeding with default order.")

            # Limit to 2 pages only
            page_number = 1
            max_pages = 2
            
            while page_number <= max_pages:
                print(f"Scraping page {page_number}...")
                
                try:
                    review_container_selector = "div[data-test-id='review-cards-container']"
                    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, review_container_selector)))
                except TimeoutException:
                    print("Timed out waiting for reviews to load.")
                    break
                
                review_cards = driver.find_elements(By.CSS_SELECTOR, f"{review_container_selector} > div.c1ofrhif")
                if not review_cards:
                    print("No review cards found on this page.")
                    break

                page_valid_reviews = 0
                page_old_reviews = 0
                
                for card in review_cards:
                    try:
                        date_str = card.find_element(By.XPATH, ".//h3/following-sibling::div").text.strip()
                        review_date = self._parse_date(date_str)

                        if not review_date: 
                            continue

                        # Track review age statistics
                        if review_date < self.start_date:
                            page_old_reviews += 1
                        elif self.start_date <= review_date <= self.end_date:
                            page_valid_reviews += 1
                            print(f"  ✓ Valid review from {review_date.date()}")
                            
                            title = card.find_element(By.CSS_SELECTOR, "h3.font-semibold").text.strip()
                            
                            # Try multiple selectors for Pros/Cons
                            try:
                                pros_text = card.find_element(By.XPATH, ".//span[contains(text(), 'Pros')]/following-sibling::p").text.strip()
                            except:
                                try:
                                    pros_text = card.find_element(By.XPATH, ".//p[preceding-sibling::*[contains(text(), 'Pros')]]").text.strip()
                                except:
                                    pros_text = "No pros available"
                            
                            try:
                                cons_text = card.find_element(By.XPATH, ".//span[contains(text(), 'Cons')]/following-sibling::p").text.strip()
                            except:
                                try:
                                    cons_text = card.find_element(By.XPATH, ".//p[preceding-sibling::*[contains(text(), 'Cons')]]").text.strip()
                                except:
                                    cons_text = "No cons available"
                            
                            review_text = f"Pros: {pros_text}\nCons: {cons_text}"
                            
                            try:
                                rating_text = card.find_element(By.CSS_SELECTOR, 'div[data-testid="rating"] span.sr2r3oj').text.strip()
                                rating = f"{rating_text}/5.0"
                            except:
                                rating = "No rating available"
                            
                            all_reviews.append({
                                'source': 'Capterra',
                                'title': title,
                                'review': review_text,
                                'date': review_date.strftime("%Y-%m-%d"),
                                'rating': rating
                            })

                    except Exception as e:
                        print(f"    Error processing review: {e}")
                        continue

                # Show progress
                print(f"  Page {page_number}: Found {page_valid_reviews} valid reviews, {page_old_reviews} old reviews")
                
                # Navigate to next page (only if not on last page)
                if page_number < max_pages:
                    if not self._goto_next_page(driver):
                        print("No more pages available.")
                        break
                    
                    page_number += 1
                    time.sleep(random.uniform(3.0, 5.0))
                else:
                    print(f"Completed scraping {max_pages} pages as requested.")
                    break

        except Exception as e:
            print(f"An error occurred during scraping: {e}")
        finally:
            try:
                if driver:
                    driver.quit()
            except:
                pass

        print(f"\nScraping completed. Found {len(all_reviews)} reviews total.")
        return all_reviews

    def _goto_next_page(self, driver):
        """Navigate to next page with multiple selector attempts."""
        next_selectors = [
            "nav a[href*='?page='] i.icon-chevron-right",
            "a[aria-label='Next page']",
            "button[aria-label='Next']",
            ".pagination .next",
            "//a[contains(text(), 'Next')]"
        ]
        
        for selector in next_selectors:
            try:
                if selector.startswith("//"):
                    next_button = driver.find_element(By.XPATH, selector)
                else:
                    next_button = driver.find_element(By.CSS_SELECTOR, selector)
                    
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
                time.sleep(1)
                driver.execute_script("arguments[0].click();", next_button)
                return True
            except:
                continue
        
        return False
        
    def _parse_date(self, date_str: str) -> datetime:
        formats_to_try = ["%B %d, %Y", "%b %d, %Y", "%m/%d/%Y", "%Y-%m-%d"]
        for fmt in formats_to_try:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None