"""
Review scrapers package
"""
from .base_scraper import BaseScraper
from .g2_scraper import G2Scraper
from .capterra_scraper import CapterraScraper

__all__ = ['BaseScraper', 'G2Scraper', 'CapterraScraper']