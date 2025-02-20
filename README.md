# Trustpilot Review Scraper
This script scrapes customer reviews from Trustpilot by collecting reviews from multiple categories, extracting company reviews based on star ratings, and saving the dataset in a structured format.

This scraper was originally based on the trustpilot webscraper used for [KBLab/robust-swedish-sentiment-multiclass](https://huggingface.co/KBLab/robust-swedish-sentiment-multiclass) which can be found [here](https://github.com/gilleti/trustpilot-scraper). However, in February 2025 it was no longer functional as it collected incorrect star ratings, creating the need for an updated version.

*Disclaimer*: This scraper was developed in February 2025. There are no promises that this will maintain its functionality.

##  Overview of What This Script Does
1. Scrapes Categories from Trustpilot to find different business sectors.
2. Finds Companies within each category.
3. Extracts Reviews from each company while filtering for star ratings (1-5 stars).
4. Ensures Balanced Data Collection:
   * Collects a maximum of 5,000 reviews per category.
   * Ensures 1,000 reviews per rating (1-5) per category.
   * Stops when 50,000 reviews are collected across all categories.
5. It also filters out
    * Empty reviews
    * One-word reviews
    * Reviews that don’t match the expected star rating
6. Saves the Scraped Data in a tab-separated file (trustpilot_reviews.tsv) with:
   * Review Text
   * Rating (1-5 stars)

## How to Use This Script
The scraper has been designed using Python 3.10.*. Compatability with other versions cannot be ensured.

1. Ensure Python is installed.
2. Install dependencies `pip install -r requirements.txt`
3. Run the script
`python scraper2.py`
4. The dataset will be saved at: `data/trustpilot_reviews.tsv`

