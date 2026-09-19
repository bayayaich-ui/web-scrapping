import logging
import shutil
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from app.scrapers.base import BaseScraper, TenderData
from app.scrapers.generic_extractor import GenericExtractor, clean_text, parse_date

logger = logging.getLogger(__name__)


class MarchesPublicsTnScraper(BaseScraper):
    extraction_method = "marchespublics_tn"

    @staticmethod
    def supports(url: str) -> bool:
        hostname = (urlparse(url).hostname or "").lower()
        return (
            hostname == "marchespublics.tn"
            or hostname.endswith(".marchespublics.tn")
            or hostname == "marchespublics.gov.tn"
            or hostname.endswith(".marchespublics.gov.tn")
        )

    def __init__(self) -> None:
        self.generic = GenericExtractor()

    def scrape(self, url: str) -> list[TenderData]:
        logger.info("Using Marches Publics Tunisie adapter", extra={"url": url})
        rendered_tenders = self._scrape_rendered_table(url)
        if rendered_tenders is not None:
            return rendered_tenders

        html = self.generic.fetch_html(url)
        soup = BeautifulSoup(html, "lxml")
        tender_table = soup.find("table", class_="table")
        if tender_table is not None and not tender_table.select("tbody tr"):
            logger.warning("Tunisia tender table has no server-rendered rows; JavaScript/API rendering is required")
            return []
        tenders = self.generic.extract_from_html(html, url)
        for tender in tenders:
            tender.extraction_method = self.extraction_method
        return tenders

    def _scrape_rendered_table(self, url: str) -> list[TenderData] | None:
        try:
            with sync_playwright() as playwright:
                browser_options = {"headless": True}
                chromium_path = shutil.which("chromium") or shutil.which("chromium-browser")
                if chromium_path:
                    browser_options["executable_path"] = chromium_path
                browser = playwright.chromium.launch(**browser_options)
                page = browser.new_page(
                    user_agent="OliveSoftTenderScraper/1.0",
                    viewport={"width": 1440, "height": 1000},
                )
                try:
                    logger.info("Rendering Tunisia tenders page with Playwright", extra={"url": url})
                    page.goto(url, wait_until="domcontentloaded", timeout=int(self.generic.timeout * 1000))
                    page.wait_for_selector("table.table tbody tr", timeout=12_000)
                    rows = page.locator("table.table tbody tr").all()
                    tenders = [self._tender_from_row(row, url) for row in rows]
                    return [tender for tender in tenders if tender.title or tender.description]
                finally:
                    browser.close()
        except PlaywrightTimeoutError:
            logger.warning("Tunisia tender rows did not render before timeout", extra={"url": url})
            return None
        except Exception:
            logger.exception("Playwright rendering failed; falling back to HTTP extraction", extra={"url": url})
            return None

    def _tender_from_row(self, row: object, page_url: str) -> TenderData:
        cells = row.locator("td").all_text_contents()
        cells = [clean_text(cell) for cell in cells]
        links = row.locator("a").all()
        detail_url = page_url
        documents: list[str] = []
        for link in links:
            href = link.get_attribute("href")
            if not href:
                continue
            absolute_url = urljoin(page_url, href)
            if absolute_url.lower().endswith((".pdf", ".doc", ".docx")):
                documents.append(absolute_url)
            elif detail_url == page_url:
                detail_url = absolute_url

        title = cells[2] if len(cells) > 2 else (cells[0] if cells else None)
        owner = cells[1] if len(cells) > 1 else None
        deadline = parse_date(cells[3] if len(cells) > 3 else None)
        published_date = parse_date(cells[4] if len(cells) > 4 else None)
        return TenderData(
            source_url=detail_url,
            title=title,
            description=clean_text(" | ".join(cell for cell in cells if cell)),
            owner=owner,
            published_date=published_date,
            deadline=deadline,
            documents=documents,
            raw_html_snippet=row.evaluate("element => element.outerHTML")[:5000],
            extraction_method=self.extraction_method,
        )
