import os
import json
import time
import random
import requests
from bs4 import BeautifulSoup
from retry_requests import retry

# Configuration
MAX_REVIEWS_PER_CATEGORY = 5_000  # Max reviews per category
# 1,000 per rating per category
REVIEWS_PER_RATING_IN_CATEGORY = MAX_REVIEWS_PER_CATEGORY // 5
TOTAL_REVIEWS_NEEDED = 50_000  # 10K per rating across all categories
REVIEW_STORAGE = {1: [], 2: [], 3: [], 4: [], 5: []}


def fetch(url):
    """Fetch HTML from URL with retries and error handling."""
    session = requests.Session()
    session = retry(session, retries=3, backoff_factor=1)
    try:
        result = session.get(url, timeout=10)
        result.raise_for_status()
        return BeautifulSoup(result.content, "html.parser")
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Request failed: {url}\nError: {e}")
        return None


def parse_soup(soup):
    """Extract JSON data from Trustpilot's embedded script tag."""
    if not soup:
        print("⚠️ Warning: Received None in parse_soup!")
        return None

    script_tag = soup.find("script", {"id": "__NEXT_DATA__"})
    if not script_tag:
        print("⚠️ Warning: No JSON data found in soup!")
        return None

    try:
        return json.loads(script_tag.text)
    except json.JSONDecodeError:
        print("⚠️ Warning: JSON parsing failed!")
        return None


def get_categories():
    """Get list of categories from Trustpilot."""
    base_url = "https://se.trustpilot.com/categories"
    category_soup = fetch(base_url)
    if not category_soup:
        return []

    data = parse_soup(category_soup)
    if not data:
        return []

    categories = data.get("props", {}).get(
        "pageProps", {}).get("categories", [])
    return [base_url + "/" + cat["categoryId"] for cat in categories]


def get_companies_from_category(category_url):
    """Fetch companies listed under a category."""
    category_soup = fetch(category_url)
    if not category_soup:
        return []

    category_data = parse_soup(category_soup)
    if not category_data:
        return []

    business_units = category_data.get("props", {}).get(
        "pageProps", {}).get("businessUnits", {})

    company_ids = []
    for v in business_units.values():
        if isinstance(v, list):
            company_ids.extend(j["identifyingName"]
                               for j in v if "identifyingName" in j)

    return company_ids


def scrape_reviews(company_id, rating, category_review_count):
    """Fetch reviews for a company at a specific star rating, ensuring a max per category."""
    url = f"https://se.trustpilot.com/review/{company_id}?stars={rating}"
    soup = fetch(url)
    if not soup:
        return []

    data = parse_soup(soup)
    if not data:
        return []

    total_pages = data.get("props", {}).get("pageProps", {}).get(
        "filters", {}).get("pagination", {}).get("totalPages", 1)

    collected_reviews = []
    for page in range(1, min(total_pages + 1, 100)):  # Trustpilot caps at ~100 pages
        if len(category_review_count[rating]) >= REVIEWS_PER_RATING_IN_CATEGORY:
            break  # Stop collecting if we reached the category rating limit

        print(
            f"  Fetching {rating}-star reviews from {company_id}, page {page}")
        time.sleep(1)

        page_url = f"{url}&page={page}"
        review_soup = fetch(page_url)
        review_data = parse_soup(review_soup)
        if not review_data:
            continue

        reviews = review_data.get("props", {}).get(
            "pageProps", {}).get("reviews", [])
        for review in reviews:
            text = review.get("text", "").strip()

            # Ignore one-word reviews
            if len(text.split()) <= 1:
                continue

            review_link = page_url  # Generate the link for the review
            category_review_count[rating].append(
                (text, rating, review_link))  # Store reviews for category

            # Stop collecting if we've reached the target per rating
            if len(category_review_count[rating]) >= REVIEWS_PER_RATING_IN_CATEGORY:
                break

        if len(category_review_count[rating]) >= REVIEWS_PER_RATING_IN_CATEGORY:
            break  # Stop fetching pages for this rating if category limit reached

    return category_review_count

# Main execution


def __main__():
    all_categories = get_categories()
    if not all_categories:
        print("⚠️ No categories found. Exiting...")
        return

    print(
        f"✅ Found {len(all_categories)} categories. Randomizing selection...")
    random.shuffle(all_categories)

    for category_url in all_categories:
        if isinstance(REVIEW_STORAGE, dict) and sum(len(v) for v in REVIEW_STORAGE.values()) >= TOTAL_REVIEWS_NEEDED:
            break  # Stop when we hit the dataset limit

        print(f"\nProcessing category: {category_url.split('/')[-1]}")
        companies = get_companies_from_category(category_url)
        if not companies:
            print("⚠️ No companies found in category. Skipping...")
            continue

        random.shuffle(companies)
        # Track reviews per rating for this category
        category_review_count = {1: [], 2: [], 3: [], 4: [], 5: []}

        for company in companies:
            if isinstance(category_review_count, dict) and sum(len(v) for v in category_review_count.values()) >= MAX_REVIEWS_PER_CATEGORY:
                break  # Stop scraping this category when it reaches 5,000 reviews

            print(f" Scraping company: {company}")

            for rating in range(1, 6):
                if len(category_review_count[rating]) >= REVIEWS_PER_RATING_IN_CATEGORY:
                    continue  # Skip if this rating is already full

                category_review_count = scrape_reviews(
                    company, rating, category_review_count)

                if isinstance(category_review_count, dict) and sum(len(v) for v in category_review_count.values()) >= MAX_REVIEWS_PER_CATEGORY:
                    break  # Stop this category when 5,000 reviews reached

        # Store collected reviews from this category into main REVIEW_STORAGE
        for rating in range(1, 6):
            REVIEW_STORAGE[rating].extend(category_review_count[rating])

        if isinstance(category_review_count, dict):
            print(
                f"Reviews collected: {sum(len(v) for v in category_review_count.values())} / {MAX_REVIEWS_PER_CATEGORY}")

            for r in range(1, 6):
                print(
                    f"   ⭐ {r}-star: {len(category_review_count[r])} reviews")
        else:
            print(
                f"⚠️ ERROR: category_review_count is a {type(category_review_count)}, expected dict!")

    print("\n✅ Finished scraping! Saving to file...")

    os.makedirs("data", exist_ok=True)

    with open("data/trustpilot_reviews.tsv", "w", encoding="utf-8") as f:
        f.write("review\trating\treview_link\n")
        for rating, reviews in REVIEW_STORAGE.items():
            for text, _, link in reviews:
                f.write(f"{text}\t{rating}\t{link}\n")

    print("✅ Dataset saved as 'data/trustpilot_reviews.tsv'!")


if __name__ == "__main__":
    __main__()
