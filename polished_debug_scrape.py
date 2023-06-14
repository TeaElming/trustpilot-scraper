import re
import os
import time
import json
import requests
import pandas as pd
from bs4 import BeautifulSoup
from retry_requests import retry

# TODO()
# Create data dir (or test) in script


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
    tags = category_soup.find("script", {"id":"__NEXT_DATA__"})
    data = json.loads(tags.text)
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
    """Get json data from soup object."""
    tags = soup.find("script", {"id":"__NEXT_DATA__"})
    data = json.loads(tags.text)
    return data

def get_company_reviews(company, stars):
    """Collects review text based on a company identifier and the number of stars a review is associated with. This is due to the fact that the script was initially designed to only collect ~*neutral*~ reviews, i.e 3 stars. A simple way to get all reviews is a for loop in main. 
    Returns... something.
    """
    return None


def __main__():
    categories = get_categories()
    # Limit to categories of interest by modifying get_categories function

    for category in categories[0:1]:
        # Category is for example https://se.trustpilot.com/categories/animals_pets
        data = []
        category_dir = category.split("/")
        category_dir = category_dir[len(category_dir)-1]
        print("Processing category: ", category_dir)
        category_specific_companies = []
        category_soup = fetch(category)
        category_data = parse_soup(category_soup)
        n_pages = category_data["props"]["pageProps"]["seoData"]["maxPages"]
        for i in range(1, n_pages):
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
                            category_specific_companies.append(company_id) # category_specific_companies is a list like ["www.horsestuff.se", "dogtrip.se", "www.hundstyrka.se"]
            i += 1
        print("There are", str(len(category_specific_companies)), " companies in category\t", category_dir)
        
        for c in category_specific_companies:
            xxx = get_company_reviews(c, 3)
            category_file = open("test/" + category_dir + ".csv", "a")
            print("\tProcessing company: ", c)
            # Collect company data
            count_soup = fetch("https://se.trustpilot.com/review/" + c + "?stars=3")
            count_data = parse_soup(count_soup)
            count_tree = count_data["props"]
            count_pages = count_tree["pageProps"]["filters"]["pagination"]["totalPages"]
            print("Company ", c, " has ", str(count_pages), " pages of 3 star reviews associated with it.")
            if count_pages > 1:
                for page in range(1, count_pages):
                    print("\tProcessing reviews from following URL: https://se.trustpilot.com/review/" + c + "?page=" + str(page) +"&stars=3")
                    time.sleep(1)
                    review_soup = fetch("https://se.trustpilot.com/review/" + c + "?page=" + str(page) +"&stars=3")
                    review_data = parse_soup(review_soup)
                    review_tree = review_data["props"]["pageProps"]
                    review_tree = review_tree["reviews"]
                    review = review_tree[0]["text"]
                    #rating = review_tree[0]["rating"]
                    rating = 3
                    data = review + "\t " + str(rating) + "\n"
                    #data = "\"" + review + "\"%%% " + str(rating) + "\n"
                    print("\t\tSaved review to list.") 
                    #category_file.write(data)
            elif count_pages == 1:
                # If it's just one page
                print("\tProcessing reviews from following URL: https://se.trustpilot.com/review/" + c + "?stars=3")
                time.sleep(1)
                review_soup = fetch("https://se.trustpilot.com/review/" + c + "?stars=3") # Specify rating if important here
                review_data = parse_soup(review_soup)
                review_tree = review_data["props"]["pageProps"]
                review_tree = review_tree["reviews"]
                review = review_tree[0]["text"]
                rating = 3
                #rating = review_tree[0]["rating"]
                data = review + "\t" + str(rating) + "\n"
                print("\t\tWrote review to file.") 
                category_file.write(data)
            else:
                continue
    


__main__()
