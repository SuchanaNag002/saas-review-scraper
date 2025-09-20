import abc
from datetime import datetime
import undetected_chromedriver as uc
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

class BaseScraper(abc.ABC):
    """
    Abstract base class for scrapers. Uses undetected-chromedriver to prevent
    common bot detection issues.
    """
    
    def __init__(self, company_name: str, start_date: datetime, end_date: datetime, is_headless: bool):
        self.company_name = company_name
        self.start_date = start_date
        self.end_date = end_date
        self.is_headless = is_headless

    def _get_driver(self) -> uc.Chrome:
        options = uc.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--no-sandbox")
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-background-timer-throttling')
        options.add_argument('--disable-backgrounding-occluded-windows')
        options.add_argument('--disable-renderer-backgrounding')
        options.add_argument('--disable-features=TranslateUI')
        options.add_argument('--disable-default-apps')
        options.add_argument('--no-first-run')
        options.add_argument('--disable-web-security')
        options.add_argument('--allow-running-insecure-content')
        
        # Set page load strategy to not wait for all resources
        caps = DesiredCapabilities.CHROME
        caps['pageLoadStrategy'] = 'eager'  # Don't wait for all resources to load
        
        if self.is_headless:
            options.add_argument('--headless=new')

        try:
            print("Initializing browser driver...")
            # Set timeout for driver initialization
            service = Service()
            service.creation_timeout = 30  # 30 second timeout
            
            driver = uc.Chrome(
                options=options, 
                version_main=140,
                service=service,
                desired_capabilities=caps
            )
            
            # Set timeouts
            driver.set_page_load_timeout(60)  # Increase timeout
            driver.implicitly_wait(10)
            
            print("Driver initialized successfully.")
            return driver
        except Exception as e:
            print(f"\nFATAL: Failed to initialize the browser driver.")
            print(f"Error: {e}")
            print("Troubleshooting tips:")
            print("1. Close all Chrome instances and try again")
            print("2. Check if Chrome version matches version_main=140")
            print("3. Try running as administrator")
            print("4. Disable antivirus temporarily")
            print("5. Try adding --headless flag")
            return None

    def _parse_date(self, date_str: str) -> datetime:
        try:
            return datetime.strptime(date_str, "%B %d, %Y")
        except ValueError:
            return None

    @abc.abstractmethod
    def scrape(self):
        raise NotImplementedError