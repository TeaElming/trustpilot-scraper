import re
import os
import time
import json
import requests
import pandas as pd
from bs4 import BeautifulSoup

def collect(url):
    OK == False
    while OK == True
        result = requests.get(url)
        if result.status_code == 200:
            OK == True
            return result
        else:
            OK == False        


def fetch(url):
    fail = True
    while fail == True:
        time.sleep(1)
        result = requests.get(url)
        status_code = result.status_code
        if status_code == 200:
            content = result.content
            soup = BeautifulSoup(result.content, "html.parser")
            fail = False
            return soup
        else:
            print("Going to sleep")
            time.sleep(2)
            fail = True

def get_categories():
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

categories = get_categories()


# Pseudokod
# fetch()
# If response = 400
# make soup


data = []

if not os.path.exists("data"):
    os.makedir("data")

for category in categories[0:1]:
    category_dir = category.split("/")
    category_dir = category_dir[len(category_dir)-1]
    if not os.path.exists("data/" + category_dir):
        os.mkdir("data/" + category_dir)

    category_specific_companies = []
    category_soup = fetch(category)
    category_tags = category_soup.find("script", {"id":"__NEXT_DATA__"})
    category_data = json.loads(category_tags.text)
    # Category is for example https://se.trustpilot.com/categories/animals_pets
    n_pages = category_data["props"]["pageProps"]["seoData"]["maxPages"]
    for i in range(1, n_pages):
        category_page = category + "?page=" + str(i)
        company_soup = fetch(category_page)
        company_tags = company_soup.find("script", {"id":"__NEXT_DATA__"})
        company_data = json.loads(company_tags.text)
        try: 

            # Collect company names
            company_tree = company_data["props"]["pageProps"]["businessUnits"]
            for k, v in company_tree.items():
                if type(v) == list:
                    for j in v:
                        company_id = j["identifyingName"]
                        if company_id not in category_specific_companies:
                            category_specific_companies.append(company_id)
        except AttributeError:
            print("COMPANY ERROR 1! There was an error with this company:" + company_id)
        i += 1
    for c in category_specific_companies:
        try:
            # Collect company data
            if not os.path.exists("data/" + category_dir + "/" + c):
                os.mkdir("data/" + category_dir + "/" + c)
            count_soup = fetch("https://se.trustpilot.com/review/" + c)
            count_tags = count_soup.find("script", {"id":"__NEXT_DATA__"})
            count_data = json.loads(count_tags.text)
            count_tree = count_data["props"]
            count_pages = count_tree["pageProps"]["filters"]["pagination"]["totalPages"]
        except AttributeError:
            print("COMPANY ERROR 2! There was an error with this company:" + c)
        for page in range(1, count_pages):
            try:
                time.sleep(1)
                review_soup = fetch("https://se.trustpilot.com/review/" + c + "?page=" + str(page) +"&stars=3") # Specify rating if important here
                review_tags = review_soup.find("script", {"id":"__NEXT_DATA__"})
                review_data = json.loads(review_tags.text)
                review_tree = review_data["props"]["pageProps"]
                review_tree = review_tree["reviews"]
                review = review_tree[0]["text"]
                rating = review_tree[0]["rating"]
                if rating == 3:
                    data.append((review, rating, category, c))
            except AttributeError:
                print("PAGE ERROR! There was an error on this page: " + "https://se.trustpilot.com/review/" + c + "?page=" + str(page))

df = pd.DataFrame(data, columns=["review", "rating", "category", "company"])
df.save_csv("ratings.csv")