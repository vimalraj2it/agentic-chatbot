import re
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
import requests
from html import unescape
from src.core.logging_config import get_logger, log_execution

logger = get_logger(__name__)

@log_execution
class ScrapingService:
    """
    Service for discovering, crawling, and cleaning website content for RAG.
    """

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "MultiAgentAssistant-Scanner/1.0"
        })

    @log_execution
    async def discover_urls(self, base_url: str) -> List[str]:
        """
        Discovers URLs from the base URL's sitemap.
        """
        sitemap_url = base_url.rstrip("/") + "/sitemap.xml"
        logger.info(f"Checking for sitemap at: {sitemap_url}")
        
        try:
            response = self.session.get(sitemap_url)
            if response.status_code != 200:
                logger.warning(f"Sitemap not found at {sitemap_url}. Status: {response.status_code}")
                return [base_url] # Fallback to just the base URL
                
            urls = []
            root = ET.fromstring(response.content)
            # Handle namespaced sitemaps
            namespace = ""
            if root.tag.startswith("{"):
                namespace = root.tag.split("}")[0] + "}"
            
            for url_node in root.findall(f".//{namespace}loc"):
                if url_node.text:
                    urls.append(url_node.text)
                    
            logger.info(f"Discovered {len(urls)} URLs from sitemap")
            return urls
        except Exception as e:
            logger.error(f"Error parsing sitemap: {e}")
            return [base_url]

    @log_execution
    async def scrape_and_clean(self, url: str) -> Dict[str, Any]:
        """
        Scrapes a URL and cleans the content based on strict rules.
        """
        logger.info(f"Scraping and cleaning: {url}")
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                logger.error(f"Failed to scrape {url}. Status: {response.status_code}")
                return {}
                
            html_content = response.text
            
            # 1. Basic cleaning (remove scripts, styles, tags)
            cleaned_text = self._clean_html(html_content)
            
            # 2. Extract metadata
            title = self._extract_title(html_content)
            
            # 3. Structure preservation (Headings, etc)
            # Since we don't have bs4, we use regex for basic structure
            sections = self._extract_sections(html_content)
            
            return {
                "title": title,
                "url": url,
                "sections": sections,
                "content": cleaned_text
            }
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return {}

    def _clean_html(self, html: str) -> str:
        """
        Cleans HTML content based on precise instructions.
        """
        # Remove scripts, styles, and comments
        content = re.sub(r'<(script|style|header|footer|nav|aside|iframe|button|modal|popup).*?>.*?</\1>', '', html, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
        
        # Remove advertisements and banners (heuristic regex)
        content = re.sub(r'<(div|section|aside)[^>]*?(id|class)=["\'][^"\']*(ad|banner|cookie|promo|popup|overlay)[^"\']*["\'][^>]*?>.*?</\1>', '', content, flags=re.DOTALL | re.IGNORECASE)
        
        # Strip all remaining tags
        content = re.sub(r'<[^>]+>', ' ', content)
        
        # Decode HTML entities
        content = unescape(content)
        
        # Normalize whitespace
        content = re.sub(r'\s+', ' ', content)
        content = content.strip()
        
        # Remove short meaningless segments (Read more, click here, etc)
        segments = content.split(". ")
        meaningful_segments = []
        noise_phrases = ["click here", "read more", "learn more", "sign up", "cookie policy"]
        
        for seg in segments:
            if len(seg.strip()) < 10:
                continue
            if any(phrase in seg.lower() for phrase in noise_phrases):
                continue
            meaningful_segments.append(seg.strip())
            
        return ". ".join(meaningful_segments)

    def _extract_title(self, html: str) -> str:
        match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
        if match:
            return unescape(match.group(1)).strip()
        return "Untitled Page"

    def _extract_sections(self, html: str) -> List[Dict[str, str]]:
        """
        Extracts headings and their subsequent content.
        """
        # Very basic regex-based heading extraction
        headings = list(re.finditer(r'<h([1-3])[^>]*>(.*?)</h\1>', html, re.IGNORECASE | re.DOTALL))
        sections = []
        
        for i, match in enumerate(headings):
            level = match.group(1)
            title = unescape(match.group(2)).strip()
            # Try to get content until next heading (this is fragile with regex but better than nothing)
            start = match.end()
            end = headings[i+1].start() if i + 1 < len(headings) else len(html)
            raw_content = html[start:end]
            clean_content = self._clean_html(raw_content)
            
            if clean_content:
                sections.append({
                    "level": level,
                    "title": title,
                    "content": clean_content
                })
        
        return sections

    def clean_url_params(self, url: str) -> str:
        """Removes tracking params like utm_source"""
        return re.sub(r'[?&](utm_|session|id)[^&]*', '', url)

scraping_service = ScrapingService()
