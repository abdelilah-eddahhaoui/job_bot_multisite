# ----------------- scrapers/linkedin/linkedin.py -----------------
"""
LinkedIn scraper for the Streamlit
• One Chromium window is shared across every keyword/location
• Playwright API runs inside a dedicated thread
• Cookies are persisted to linkedin_state.json on every scrape
"""
from __future__ import annotations

import concurrent.futures
import logging
import os, random, re, time
import html2text
from pathlib import Path
from typing import List, Optional, Tuple
from urllib.parse import quote_plus

import pandas as pd
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

from scrapers.base import BaseScraper
from scrapers.models import JobPosting
from scrapers.linkedin.selectors import (
    JOB_CARD, FIRST_CARD, SCROLL_BOX,
    DESCRIPTION_BOX, SHOW_MORE_BUTTON,
    ACCOUNT_PICKER_BTN, JOBS_NAV
)

log = logging.getLogger(__name__)
_JOBS_RE = re.compile(r"https?://www\.linkedin\.com/jobs/view/(\d+)")


##### ---------------- HELPERS (start) ---------------- #####

## Adds a human-like randomized pause between actions to avoid bot detection ##
def _sleep_random(delay_range: Tuple[float, float]) -> None:
    time.sleep(random.uniform(*delay_range))

## Modifies navigator.webdriver to undefined (used by LinkedIn to detect bots) ##
def _apply_stealth(ctx) -> None:
    ctx.add_init_script(
        "Object.defineProperty(navigator,'webdriver',{get:()=>undefined});"
    )

## Returns a randomly chosen User-Agent string to avoid detection ##
def _random_user_agent() -> str:
    return random.choice(
        [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5_1) AppleWebKit/605.1.15 "
            "(KHTML, like Gecko) Version/17.1 Safari/605.1.15",
        ]
    )

## Uses html2text to convert the raw job description (HTML) to plain text ##
def _html_to_markdown(raw_html: str) -> str:
    """Convert Linkedin’s rich HTML pane to clean markdown/plain-text."""
    h = html2text.HTML2Text()
    h.unicode_snob = True
    h.body_width   = 0          # keep original wrapping
    h.ignore_links = True
    h.ignore_images = True
    md = h.handle(raw_html)
    # collapse 3+ consecutive blank lines → max 2
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md.strip()

def _canonical_job_url(raw: str) -> str:
    """
    - prepend https://www.linkedin.com if the link is relative
    - strip every query string & fragment
    - keep only “…/jobs/view/<numeric-id>/”
    """
    import re, urllib.parse as _up

    if raw.startswith("/"):
        raw = "https://www.linkedin.com" + raw

    # drop ?… and #… parts
    raw = _up.urlsplit(raw)._replace(query="", fragment="").geturl()

    m = re.search(r"/jobs/view/(\d+)", raw)
    return f"https://www.linkedin.com/jobs/view/{m.group(1)}/" if m else raw

##### ---------------- HELPERS (end) ---------------- #####




# ───────────────────────── scraper CLASS using abstract BaseScraper() class for 'skull'  ────────────────────────── #

class LinkedinScraper(BaseScraper):
    platform = "Linkedin"

    def __init__(
            self,
            *,
            headless: bool = True,
            output_dir: os.PathLike | str = "results",
            delay_range: Tuple[float, float] = (3.5, 7.0),
            storage_path: os.PathLike | str = "linkedin_state.json",
        ) -> None:
        super().__init__(headless=headless, output_dir=output_dir)

        self.delay_range = delay_range
        self.storage_path = Path(storage_path)
        if not self.storage_path.exists():
            raise RuntimeError(
                f"Cookie file '{self.storage_path}' not found. "
                "Run linkedin_login_helper.py first to create it."
            )

        # single worker keeps browser alive for the whole dashboard session
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self._pw = self._browser = self._context = self._page = None  # lazy init
        

##### ---------------- public API (start) ---------------- #####
    
## Runs _scrape_internal() inside a thread (main core in _scrape_internal() ##
    def scrape(
        self,
        *,
        keyword: str,
        location: str,
        limit: int,
        hours_old: int,
        ea_application: bool,
    ) -> pd.DataFrame:
        """Thread-safe entry point called from Streamlit."""
        fut = self._executor.submit(
            self._scrape_internal, keyword, location, limit, hours_old, ea_application
        )
        return fut.result()

## Closes browser and threadpool when the scraper is no longer needed ##
    def close(self):
        """Shut down browser & thread (call once at program end)."""
        def _shutdown():
            if self._browser:
                self._browser.close()
            if self._pw:
                self._pw.stop()

        self._executor.submit(_shutdown).result()
        self._executor.shutdown(wait=True)

##### ---------------- public API (end) ---------------- #####



##### -------------- INTERNAL (worker thread) (start) -------------- #####
    
    def _get_page(self):
        if self._page:
            return self._page

        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(
            headless=self.headless,
            args=["--disable-blink-features=AutomationControlled", "--start-maximized"],
        )
        self._context = self._browser.new_context(
            viewport={"width": 1280, "height": 1024},
            user_agent=_random_user_agent(),
            locale="en-US",
            storage_state=str(self.storage_path),
        )
        _apply_stealth(self._context)

        page = self._context.new_page()
        if not self._ensure_logged_in(page):
            raise RuntimeError("Saved cookies expired – refresh via helper script.")
        self._page = page
        return page

    def _scrape_internal(
        self,
        keyword: str,
        location: str,
        limit: int,
        hours_old: int,
        ea_application: bool,
    ) -> pd.DataFrame:

## Open Browser Page ##
        page = self._get_page()
        
## Cookie storage after 1st Login ##
        self._context.storage_state(path=str(self.storage_path))  # persist cookies

## Search URL construction ##

## LINKEDIN SETTINGS FOR SEARCH ##
        ea_application = str(ea_application)
        seconds_old = hours_old * 3600
        if location == "France":
            location_id = 105015875
        elif location == "Germany":
            location_id = 101282230
        elif location == "Spain":
            location_id = 105646813
        elif location == "Italy":
            location_id = 103350119 
        elif location == "Netherlands":
            location_id = 102890719
        elif location == "Australia":
            location_id = 101452733
        elif location == "USA":
            location_id = 103644278
        elif location == "UK":
            location_id = 101165590
        elif location == "Sweden":
            location_id = 105117694
        elif location == "Denmark":
            location_id = 104514075
        elif location == "Switzerland":
            location_id = 106693272        
        elif location == "Luxembourg":
            location_id = 104042105
            
## LINKEDIN SETTINGS FOR SEARCH ##
        
        search_url = (
            "https://www.linkedin.com/jobs/search/"
            f"?f_AL={quote_plus(ea_application)}"                     # EasyApply filter
            "&f_E=2%2C4"                                              # Experience level (2 = Entry, 4 = Mid-Senior)
            f"&f_TPR=r{quote_plus(str(seconds_old))}"                 # Time posted (TPR)
            f"&geoId={quote_plus(str(location_id))}"                  # Geo Location
            f"&keywords={quote_plus(keyword)}"
            "&origin=JOB_SEARCH_PAGE_JOB_FILTER&refresh=true&sortBy=R&spellCorrectionEnabled=true"
        )
        
### SEARCH URL EXMP ###
# https://www.linkedin.com/jobs/search/?f_AL=true&keywords=Cfd&origin=JOB_SEARCH_PAGE_JOB_FILTER&refresh=true&sortBy=R&spellCorrectionEnabled=true&start=50
### SEARCH URL EXMP ###
       
## Page loading ##
        page.goto(search_url, wait_until="domcontentloaded")
        page.eval_on_selector("body", "(b)=>b.scrollTo(0,2000)")
        _sleep_random((0.3, 0.6))

## If LinkedIn bounces to "../feed", it clicks the Jobs nav manually and tries again ##
        if "/feed" in page.url:  # bounce fallback
            jobs_nav = page.query_selector(JOBS_NAV)
            if not jobs_nav:
                raise RuntimeError("Jobs nav link missing – LinkedIn changed layout.")
            jobs_nav.click()
            page.wait_for_url("**/jobs/**", timeout=15_000)
            page.goto(search_url, wait_until="domcontentloaded")
        _sleep_random(self.delay_range)

## Dynamically identifies the HTML container holding all job cards, then ensures jobs are visible ##
        container_sel = self._detect_container(page)
        self._scroll_until_first_card(page)
        page.wait_for_selector(container_sel, timeout=60_000)
        postings: List[JobPosting] = []
        card_sel = f"{container_sel} {JOB_CARD}"


## Loop Through Job Cards ##
## For each job : click the card, click "Show More" if needed, scroll inside the job description, ##
## extract raw HTML, convert to markdown, parse metadata (title, company, location), 
## extract email addresses (regex), check for "Easy Apply" button → then build a JobPosting object. ##
        for card in page.query_selector_all(card_sel)[:limit]:
            _sleep_random((0.8, 1.6))
            card.click()
            _sleep_random((0.4, 1.0)) 

            # expand “Show more” buttons
            for btn in page.query_selector_all(SHOW_MORE_BUTTON):
                if btn.is_visible():
                    btn.click()
                    _sleep_random((0.4, 1.0))

            # locate description container
            box = page.query_selector(DESCRIPTION_BOX)
            if not box:
                log.debug("description box missing – skipped")
                continue

            # scroll box to force lazy loading
            page.evaluate(
                """
                (el) => {
                    const total = el.scrollHeight;
                    let y = 0;
                    const step = total / 12;          // 12 small steps
                    function smoothScroll() {
                        y += step;
                        el.scrollTo({ top: y, behavior: 'smooth' });
                        if (y < total) setTimeout(smoothScroll, 350 + Math.random()*250);
                    }
                    smoothScroll();
                }
                """,
                box,
            )
            _sleep_random((0.5, 1.2))
            page.wait_for_timeout(5000)

            raw_html = box.inner_html()
            desc_txt = _html_to_markdown(raw_html)
            if len(desc_txt) < 50:        
                log.debug("desc too short – skipped")
                continue


            meta = self._parse_card(card)
            if not meta:
                continue

            emails_found = re.findall(
                r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", desc_txt
            )

            postings.append(
                JobPosting(
                    title=meta.title,
                    company=meta.company,
                    location=meta.location,
                    job_id=meta.job_id,
                    job_url=meta.job_url,
                    listed_at=meta.listed_at,
                    description=desc_txt,
                    emails=emails_found or None,
                )
            )

        df = self._to_dataframe(postings)

        csv_path = self._persist_dataframe(
            df, name=f"linkedin_{keyword}_{location}_{int(time.time())}"
        )
        log.info("[LinkedInScraper] Saved %d rows → %s", len(df), csv_path)
        return df
    
##### -------------- INTERNAL (worker thread) (end) -------------- #####



##### -------------- mini-HELPERS (worker) (start) -------------- #####

    def _ensure_logged_in(self, page) -> bool:
        page.goto("https://www.linkedin.com/feed", wait_until="domcontentloaded")
        if page.url.startswith("https://www.linkedin.com/feed"):
            return True
        if ("login" in page.url or "checkpoint" in page.url) and self._dismiss_account_picker(page):
            return True
        if "login" in page.url or "uas/login" in page.url:
            print("🛑  Manual login required – window paused.")
            page.pause()
            return page.url.startswith("https://www.linkedin.com/feed")
        return False

    def _scroll_until_first_card(self, page, max_scrolls: int = 15) -> bool:
        scroll_box = page.query_selector(SCROLL_BOX)
        if not scroll_box:
            return False
        for step in range(max_scrolls):
            if page.query_selector(JOB_CARD):
                return True
            scroll_box.evaluate("(el,y)=>el.scrollTo(0,y)", (step + 1) * 600)
            _sleep_random((0.15, 0.35))
        return False

    def _detect_container(self, page) -> str:
        page.wait_for_selector(FIRST_CARD, timeout=60_000)
        li = page.query_selector(FIRST_CARD)
        ul = li.evaluate_handle(
            """(n)=>{let e=n;while(e&&!['UL','DIV'].includes(e.tagName))e=e.parentElement;return e;}"""
        )
        tag = ul.evaluate("e=>e.tagName.toLowerCase()")
        cls = ul.evaluate("e=>e.className").strip().replace("  ", " ")
        return f"{tag}{'.' + '.'.join(cls.split()) if cls else ''}"

    def _dismiss_account_picker(self, page) -> bool:
        btn = page.query_selector(ACCOUNT_PICKER_BTN)
        
        if not btn:
            return False
        btn.click()
        try:
            page.wait_for_url(r".*/feed.*", timeout=10_000)
            return True
        except PWTimeout:
            return False

    def _parse_card(self, card) -> Optional[JobPosting]:
        try:
            job_div = card.query_selector("div[data-job-id]")
            job_id = job_div.get_attribute("data-job-id") if job_div else None
            
            link_elem     = card.query_selector("a.job-card-container__link")
            job_url   = _canonical_job_url(link_elem.get_attribute("href")) if link_elem else None

            title = link_elem.inner_text().splitlines()[0].strip() if link_elem else ""
            company_el = card.query_selector(
                "div.artdeco-entity-lockup__subtitle, span.job-card-container__primary-description"
            )
            company = company_el.inner_text().strip() if company_el else ""
            loc_el = card.query_selector("ul.job-card-container__metadata-wrapper li")
            location = loc_el.inner_text().strip() if loc_el else ""
            time_el = card.query_selector("time")
            listed_at = time_el.get_attribute("datetime") if time_el else None

            return JobPosting(
                title=title,
                company=company,
                location=location,
                job_id=job_id,
                job_url=job_url,
                listed_at=listed_at,
            )
        except Exception as exc:
            log.warning("card parse failed → %s", exc)
            return None

##### -------------- mini-HELPERS (worker) (end) -------------- #####
