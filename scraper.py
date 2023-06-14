import os
import pandas as pd
import time
import json
import requests
from bs4 import BeautifulSoup
from retry_requests import retry

# Minimal Trustpilot scraper
# Outputs tsv file consisting of two columns: review, rating

def fetch(url):
    """Get function with some native request throttling.
    Inputs a url and returns a BeautifulSoup object.
    """
    session = requests.Session()
    session = retry(session, retries=3, backoff_factor=1)
    result = session.get(url)
    if result:
        soup = BeautifulSoup(result.content, "html.parser")
        return soup
    else:
        None

def get_categories():
    """Get updated list of categories, i.e "Byggmaterial" or "Tandvård".
    Returns a list of URLs, for example https://se.trustpilot.com/categories/architects_engineers
    """
    top_category_url = "https://se.trustpilot.com/categories"
    category_soup = fetch(top_category_url)
    data = parse_soup(category_soup)
    tree = data["props"]
    all_categories = []
    cats = tree["pageProps"]["categories"]
    for category in cats:
        all_categories.append(category["categoryId"])
    category_urls = []
    for cat in all_categories:
        category_url = top_category_url + "/" + cat
        category_urls.append(category_url) # All category URLs collected from site
    return category_urls

def parse_soup(soup):
    """Get embedded json data from soup object."""
    tags = soup.find("script", {"id":"__NEXT_DATA__"})
    data = json.loads(tags.text)
    return data

def __main__():
    categories = get_categories()
    # Limit to categories of interest by modifying get_categories function

    for category in categories[0:1]:
        dfs = []
        # Category is for example https://se.trustpilot.com/categories/animals_pets
        data = []
        category_dir = category.split("/")
        category_dir = category_dir[len(category_dir)-1]
        print("Processing category: ", category_dir)
        category_specific_companies = []
        category_soup = fetch(category)
        category_data = parse_soup(category_soup)
        n_pages = category_data["props"]["pageProps"]["seoData"]["maxPages"]
        for i in range(1, n_pages): # Iterate over number of category pages
            category_page = category + "?page=" + str(i)
            company_soup = fetch(category_page)
            company_data = parse_soup(company_soup)
            # Collect company name identifiers here
            company_tree = company_data["props"]["pageProps"]["businessUnits"]
            for k, v in company_tree.items():
                if type(v) == list:
                    for j in v:
                        company_id = j["identifyingName"]
                        if company_id not in category_specific_companies:
                            category_specific_companies.append(company_id)
                            # category_specific_companies is a list like ["www.horsestuff.se", "dogtrip.se", "www.hundstyrka.se"]
            i += 1
        print("There are", str(len(category_specific_companies)), " companies in category\t", category_dir)
        
        for c in category_specific_companies: # Iterate over companies in categories            
            category_file = open("data/" + category_dir + ".tsv", "a") # Modify dir here
            print("\tProcessing company: ", c)
            # Collect company data

            for rating in range(1, 5): # Modify this line if you're interested in a secific category. If not, we iterate over all ratings.
                print("\t\tProcessing ", str(rating), " star reviews.")
                count_soup = fetch("https://se.trustpilot.com/review/" + c + "?stars=" + str(rating))
                count_data = parse_soup(count_soup)
                count_tree = count_data["props"]
                count_pages = count_tree["pageProps"]["filters"]["pagination"]["totalPages"]
                print("\t\t\tCompany ", c, " has ", str(count_pages), " pages of ", str(rating), " star reviews associated with it.")
                for page in range(1, count_pages+1):
                    print("\t\t\tProcessing reviews from following URL: https://se.trustpilot.com/review/" + c + "?page=" + str(page) +"&stars=" + str(rating))
                    time.sleep(1)
                    review_soup = fetch("https://se.trustpilot.com/review/" + c + "?page=" + str(page) +"&stars=" + str(rating))
                    review_data = parse_soup(review_soup)
                    review_tree = review_data["props"]["pageProps"]
                    review_tree = review_tree["reviews"]
                    review = review_tree[0]["text"]
                    data = review + "\t " + str(rating) + "\n"
                    category_file.write(data)
                    print("\t\t\tSaved review to file.")
                    print()



is_dir = os.path.exists("data")
if not is_dir:
    os.mkdir("data")
    print("Data dir created.")

__main__()
