import abc
from datetime import datetime
import undetected_chromedriver as uc

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
        # Initialize an undetected chrome instance to appear more like a real user.
        options = uc.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--no-sandbox")
        
        if self.is_headless:
            options.add_argument('--headless=new')

        driver = uc.Chrome(options=options)
        return driver

    def _parse_date(self, date_str: str) -> datetime:
        try:
            return datetime.strptime(date_str, "%b %d, %Y")
        except ValueError:
            return None

    @abc.abstractmethod
    def scrape(self):
        raise NotImplementedError