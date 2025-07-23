# scrapers/linkedin/selectors.py
"""
All CSS / attribute selectors used by the LinkedIn scraper.
"""

# ──────────────────────────────────────────────────────────
#  SEARCH RESULTS  (left-hand column)
# ──────────────────────────────────────────────────────────
# ancestor element that wraps every <li data-job-id …>
RESULTS_CONTAINER = (
    "div.jobs-search-results-list, "
    "ul.jobs-search__results-list, "
    "ul.scaffold-layout__list"
)

# each job card
JOB_CARD   = "li[data-occludable-job-id], li[data-job-id]"
FIRST_CARD = "li[data-occludable-job-id], div[data-job-id]"

# the scrollable <div> / <ul> that lazy-loads more cards
SCROLL_BOX = RESULTS_CONTAINER       # same element

# ──────────────────────────────────────────────────────────
#  DETAIL PANE  (right-hand side)
# ──────────────────────────────────────────────────────────

DESCRIPTION_BOX = (
    "div.jobs-description-content, "
    "div.jobs-description__content, "
    "section.jobs-description-content__text, "
    "section.show-more-less-html__markup, "
    "div[data-test-id='job-details-description'], "
    "div.mt4"                           # 2025 layout experiment
)


# ──────────────────────────────────────────────────────────
#  MISC  (login picker, nav link, etc.)
# ──────────────────────────────────────────────────────────

SHOW_MORE_BUTTON = (
    "button[data-test-id='show-more-button'], "
    "button.show-more-less-html__button"
)

NEXT_BTN_SEL = (
    "button[aria-label='Next'],"
    "button[aria-label='Continue'],"
    "button[aria-label='Review your application'],"
    "button[aria-label='Review']"
)

SUBMIT_BTN_SEL = (
    "button[aria-label='Submit application'],"
    "button[aria-label='Submit']"
)

ACCOUNT_PICKER_BTN = (
    "button[data-test*='previous_account_login'], "
    "button[aria-label^='Continue as'], "
    "button[title*='Sign in as']"
)

JOBS_NAV = "a[data-test-global-nav-link='jobs']"

