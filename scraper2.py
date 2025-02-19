import os
import json
import time
import random
import requests
from bs4 import BeautifulSoup
from bs4.element import Tag
from retry_requests import retry
from typing import List

# Configuration
MAX_REVIEWS_PER_CATEGORY =  5_000  # Max reviews per category
REVIEWS_PER_RATING_IN_CATEGORY = MAX_REVIEWS_PER_CATEGORY //  5  # 1,000 per rating per category
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


def get_categories():
    """Get list of categories from Trustpilot."""
    base_url = "https://se.trustpilot.com/categories"
    category_soup = fetch(base_url)
    if not category_soup:
        return []

    # Use "attrs" in the find call; ignore type checking here.
    script_tag = category_soup.find("script", attrs={"id": "__NEXT_DATA__"})  # type: ignore
    if not script_tag:
        return []

    try:
        data = json.loads(script_tag.text)
        categories = data.get("props", {}).get("pageProps", {}).get("categories", [])
        return [base_url + "/" + cat["categoryId"] for cat in categories]
    except json.JSONDecodeError:
        return []


def get_companies_from_category(category_url):
    """Fetch companies listed under a category."""
    category_soup = fetch(category_url)
    if not category_soup:
        return []

    script_tag = category_soup.find("script", attrs={"id": "__NEXT_DATA__"})  # type: ignore
    if not script_tag:
        return []

    try:
        data = json.loads(script_tag.text)
        business_units = data.get("props", {}).get("pageProps", {}).get("businessUnits", {})
        return [
            j["identifyingName"]
            for v in business_units.values()
            if isinstance(v, list)
            for j in v
            if "identifyingName" in j
        ]
    except json.JSONDecodeError:
        return []


def scrape_reviews(company_id, rating, category_review_count):
    """Fetch reviews for a company at a specific star rating, ensuring a max per category."""
    url = f"https://se.trustpilot.com/review/{company_id}?stars={rating}"
    soup = fetch(url)
    if not soup:
        return category_review_count

    # Annotate review_containers as List[Tag] and ignore type errors for the find_all call.
    review_containers: List[Tag] = soup.find_all("article", attrs={"data-service-review-card-paper": "true"})  # type: ignore

    for container in review_containers:
        if len(category_review_count[rating]) >= REVIEWS_PER_RATING_IN_CATEGORY:
            break  # Stop collecting if we reached the rating limit

        # Extract the actual rating from the review
        rating_tag = container.find("div", attrs={"class": "styles_reviewHeader__PuHBd"})  # type: ignore
        actual_rating = None

        if rating_tag and isinstance(rating_tag, Tag):
            attr_val = rating_tag.get("data-service-review-rating")
            if attr_val is not None:
                try:
                    # Cast the attribute value to string before converting to int
                    actual_rating = int(str(attr_val))
                except (TypeError, ValueError):
                    continue  # Skip if rating extraction fails

                if actual_rating != rating:
                    continue  # Skip reviews that don't match the expected rating
        else:
            continue  # Skip if there's no valid rating tag

        # Extract review text safely
        review_text_tag = container.find("p", attrs={"data-service-review-text-typography": "true"})  # type: ignore
        if review_text_tag and isinstance(review_text_tag, Tag) and review_text_tag.text:
            review_text = review_text_tag.text.strip()
            # Ignore one-word reviews
            if len(review_text.split()) > 1:
                category_review_count[rating].append((review_text, rating))

    return category_review_count


def __main__():
    all_categories = get_categories()
    if not all_categories:
        print("⚠️ No categories found. Exiting...")
        return

    print(f"✅ Found {len(all_categories)} categories. Randomizing selection...")
    random.shuffle(all_categories)

    for category_url in all_categories:
        if sum(len(v) for v in REVIEW_STORAGE.values()) >= TOTAL_REVIEWS_NEEDED:
            break  # Stop when we hit the dataset limit

        print(f"\n🔍 Processing category: {category_url.split('/')[-1]}")
        companies = get_companies_from_category(category_url)
        if not companies:
            print("⚠️ No companies found in category. Skipping...")
            continue

        random.shuffle(companies)
        category_review_count = {1: [], 2: [], 3: [], 4: [], 5: []}  # Track reviews per rating for this category

        for company in companies:
            if sum(len(v) for v in category_review_count.values()) >= MAX_REVIEWS_PER_CATEGORY:
                break  # Stop scraping this category when it reaches the max reviews

            print(f"🏢 Scraping company: {company}")

            for rating in range(1, 6):
                if len(category_review_count[rating]) >= REVIEWS_PER_RATING_IN_CATEGORY:
                    continue  # Skip if this rating is already full

                category_review_count = scrape_reviews(company, rating, category_review_count)

                if sum(len(v) for v in category_review_count.values()) >= MAX_REVIEWS_PER_CATEGORY:
                    break  # Stop this category when max reviews reached

        # Store collected reviews from this category into main REVIEW_STORAGE
        for rating in range(1, 6):
            REVIEW_STORAGE[rating].extend(category_review_count[rating])

        print(f"✅ Category {category_url.split('/')[-1]} scraping complete!")
        print(f"   📊 Reviews collected: {sum(len(v) for v in category_review_count.values())} / {MAX_REVIEWS_PER_CATEGORY}")
        for r in range(1, 6):
            print(f"   ⭐ {r}-star: {len(category_review_count[r])} reviews")

    print("\n✅ Finished scraping! Saving to file...")

    os.makedirs("data", exist_ok=True)
    with open("data/trustpilot_reviews.tsv", "w", encoding="utf-8") as f:
        f.write("review\trating\n")
        for rating, reviews in REVIEW_STORAGE.items():
            for text, _ in reviews:
                f.write(f"{text}\t{rating}\n")

    print("✅ Dataset saved as 'data/trustpilot_reviews.tsv'!")


if __name__ == "__main__":
    __main__()
