import re
import os
import time
import json
import requests
from retry_requests import retry
#from urllib3 import Retry
import pandas as pd
from bs4 import BeautifulSoup

def fetch(url):
    session = requests.Session()
    session = retry(session, retries=3, backoff_factor=1)
    result = session.get(url)
    if result:
        soup = BeautifulSoup(result.content, "html.parser")
        return soup
    else:
        None

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

# [0:1]
# [1:2]
for category in categories[1:2]:
    data = []
    category_dir = category.split("/")
    category_dir = category_dir[len(category_dir)-1]
    #print("Starting with category: ", category_dir)
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
        # Collect company names
        company_tree = company_data["props"]["pageProps"]["businessUnits"]
        for k, v in company_tree.items():
            if type(v) == list:
                for j in v:
                    company_id = j["identifyingName"]
                    if company_id not in category_specific_companies:
                        category_specific_companies.append(company_id)
        i += 1
    
    #print("Category ", category_dir, "has ", str(len(category_specific_companies)), " companies in it.")
    
    for c in category_specific_companies:
        category_file = open("data/" + category_dir + ".csv", "a")
        print("Processing company: ", c)
        # Collect company data
        count_soup = fetch("https://se.trustpilot.com/review/" + c + "?stars=3")
        count_tags = count_soup.find("script", {"id":"__NEXT_DATA__"})
        count_data = json.loads(count_tags.text)
        count_tree = count_data["props"]
        count_pages = count_tree["pageProps"]["filters"]["pagination"]["totalPages"]
        print("Company ", c, " has ", str(count_pages), " pages of 3 star reviews associated with it.")
        if count_pages > 1:
            for page in range(1, count_pages):
                print("\tProcessing reviews from following URL: https://se.trustpilot.com/review/" + c + "?page=" + str(page) +"&stars=3")
                time.sleep(1)
                review_soup = fetch("https://se.trustpilot.com/review/" + c + "?page=" + str(page) +"&stars=3")
                review_tags = review_soup.find("script", {"id":"__NEXT_DATA__"})
                review_data = json.loads(review_tags.text)        
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
            review_tags = review_soup.find("script", {"id":"__NEXT_DATA__"})
            review_data = json.loads(review_tags.text)        
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
    
