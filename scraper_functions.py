# -*- coding: utf-8 -*-
"""
Created on Tue Oct 27 17:10:33 2020

@author: Anastasia
"""

#Import all packages

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from daterangeparser import parse
import datetime
import requests
import random
import time 
import re 
import numpy as np 

def get_url_list(search_list):
    """Gets a list of URLs for Etsy and a list of terms to append to the 'category' column from an input of a list of search term strings. Spaces will be accounted for.   
    """
    url_list = []
    term_list=[]
    for term in search_list:
        url_list.append('https://www.etsy.com/uk/search?q=' + re.sub("\s", "+", term))
        term_list.append(term)
    return url_list, term_list
    
def close_popup(driver):
    """Closes the 'privacy settings' popup on the homepage of search results. Takes the Chromdriver as an input.   
    """
    pop_up_xpath = "//*[@id='gdpr-single-choice-overlay']/div/div[2]/div[2]/button"
    try:
        driver.find_element_by_xpath(pop_up_xpath).click()
    except:
        pass
    
def open_page(driver, URL):
    """Opens a webpage given a driver and a URL. This function uses the 'close_popup' function to get past the privacy setting popup. It also accounts for potential IP blocks by sleeping for a random amount of time between 10 and 15 seconds with each page opened.   
    """
    for i in range(3): 
        try: 
          random_sleep_link = random.uniform(10, 15)
          time.sleep(random_sleep_link)
          driver.get(URL)
          time.sleep(3)
          close_popup(driver)
      
        except requests.exceptions.RequestException: 
          random_sleep_except = random.uniform(240,360)
          print("I've encountered an error! I'll pause for"+str(random_sleep_except/60) + " minutes and try again \n")
          time.sleep(random_sleep_except) 
          continue 
        else: 
          break 
    else: 
        raise Exception("Something really went wrong here... I'm sorry.") 

def get_links(driver):
    """This function finds all of the links to listings on an Etsy page and returns a list composed of the text of the href attribute. It takes your webdriver as an input.
    """
    link_list = []
    links = driver.find_elements_by_xpath('//a[starts-with(@href, "https://www.etsy.com/uk/listing/")]')
    for link in links:
        link_text = link.get_attribute("href")
        link_list.append(link_text)
    return link_list

def scrape_link_details(driver,link):
    """Opens a link to a listing and scrapes all of the pertinent details. Returns 1) the number of sales made by the shop, 2) the number of this item currently in people's baskets, 3) the description of the item, 4) the average number of days between today and when the item arrives, 5) the cost of delivery, 6) whether returns are accepted, 7) the country where the item is dispatched from, and 8) how many images the listing has.   
    """
    for i in range(3): 
        try: 
          random_sleep_link = random.uniform(5,7)
          time.sleep(random_sleep_link)
          windows_before  = driver.current_window_handle 
          driver.execute_script("window.open('" + link +"');")
          print('opened window')
          windows_after = driver.window_handles
          new_window = [x for x in windows_after if x != windows_before][0]
          print('got new deets')
          driver.switch_to.window(new_window) 
          loaded = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "gnav-search")))
          
          try:
                sales = loaded.find_elements_by_xpath('//div[@id="listing-page-cart"]//div[contains(@class, "wt-display-inline-flex-xs")]//span[contains(text(), "sale")]')
                s = sales[0].text
                num_sales = s.split(" ")[0]
          except:
                num_sales = 0
                        
          try:
                num_basket = 0
                basket = driver.find_elements_by_xpath('//div[@data-appears-component-name="listings_nudge_incartonly"]')
                x = basket[0].text
                if len(x) > 0:
                    num_basket = re.sub(r'[^0-9]', '', x)
          except:
                num_basket = 0
            
          try:
                description = loaded.find_element_by_xpath("//meta[@name='description']")
                descriptions = description.get_attribute("content")
          except:
                descriptions = np.nan


          try:
                arrivals = loaded.find_elements_by_xpath('//div[@data-appears-component-name="listing_page_estimated_delivery_date"]//button')

                days_to_arrival = try_to_parse_arrival_date(arrivals)
                
                if days_to_arrival is None:
                    arrivals = loaded.find_elements_by_xpath('//div[@data-appears-component-name="listing_page_estimated_delivery_date"]//p[@data-edd-absolute]')
                    days_to_arrival = try_to_parse_arrival_date(arrivals)

                if days_to_arrival is None:
                    arrivals = loaded.find_elements_by_xpath('//div[@data-selector="listing-page-buybox-quick-delivery-content"]//span[@aria-describedby]')
                    days_to_arrival = try_to_parse_arrival_date(arrivals)
                    
                if days_to_arrival is None:
                    days_to_arrival = np.nan
          except:
                days_to_arrival = np.nan
            
          try:
                delivery = loaded.find_element_by_xpath("//*[contains(text(), 'Cost to deliver')]/..").text
                if 'Free' in delivery or 'free' in delivery:
                    cost_delivery = 0
                else:
                    match = re.search(r'\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})', delivery).group(0)
                    cost_delivery = float(match)
          except:
                cost_delivery = np.nan
            
          try:
                return_accepteds = loaded.find_elements_by_xpath('//div[@id="shipping-variant-div"]//span[contains(text(), "eturns")]/..')
                if len(return_accepteds) == 0:
                    return_accepteds = loaded.find_elements_by_xpath('//button[contains(text(), "eturns") and contains(text(), "changes")]/..')
                if 'ccepted' in return_accepteds[0].text:
                    returns_accepted = 1
          except:
                returns_accepted = 0
            
          try:
                dispatch = loaded.find_element_by_xpath("//*[@id='shipping-variant-div']/div/div[2]/div[7]").text
                d_split = dispatch.split(" ")[2:]
                d_join = " ".join(d_split)
                dispatch_from = d_join
          except:
                dispatch_from = np.nan
            
          try:
                images = loaded.find_element_by_xpath("//ul[starts-with(@class, 'wt-list-unstyled wt-display-flex-xs')]")
                i_list = images.find_elements_by_xpath("//li[@class='wt-mr-xs-1 wt-mb-xs-1 wt-bg-gray wt-flex-shrink-xs-0 wt-rounded carousel-pagination-item-v2']")
                count_images = len(i_list)
          except:
                count_images = 1
          driver.close() # close the window
          driver.switch_to.window(windows_before) # switch_to the parent_window_handle
          print('switched')
          
        except requests.exceptions.RequestException: #if anything weird happens...#
          random_sleep_except = random.uniform(240,360)
          print("I've encountered an error! I'll pause for"+str(random_sleep_except/60) + " minutes and try again \n")
          time.sleep(random_sleep_except) #sleep the script for x seconds and....#
          continue #...start the loop again from the beginning#
      
        else: #if the try-part works...#
          break #...break out of the loop#
          print('broke out of the loop')

    else: #if x amount of retries on the try-part don't work...#
        raise Exception("Something really went wrong here... I'm sorry.") #...raise an exception and stop the script# 
    
    return num_sales, num_basket, descriptions, days_to_arrival, cost_delivery, returns_accepted, dispatch_from, count_images
    
def try_to_parse_arrival_date(arrival_elements):
    try:
        arrival = arrival_elements[0]
        arrival_range = arrival.text
        start, end = parse(arrival_range)
        average = start + (end - start)/2
        today = datetime.date.today()
        diff = average.date() - today
        return diff.days
    except:
        return None

def get_main_page(driver, result, term):
    """Scrapes the details of the search page. This function takes 3 arguments as inputs: 1) your webdriver, 2) the location of the contents area of the Etsy search page, and 3) the search term you're currently scrubbing for. It returns 65 object lists for each of the following: 1) titles of the listings, 2) whether the listings are ads, 3) the names of the listing shops, 3) the star rating of the shops, 4) the number of reviews the shops have, 5) the prices of the objects, 6) whether the listings are bestsellers, and 7) the category of the search (which will be the term you've input)  
    """
    titles = result.find_element_by_css_selector("div > a[href]").get_attribute("title")
    
    shop_name = np.nan
    is_ad = 0
    shop_name_elements = result.find_elements_by_xpath('.//div[contains(@class, "wt-text-caption")]/p[@aria-role]')
    if len(shop_name_elements) > 0:
        shop_name_element = shop_name_elements[0]
        shop_name = shop_name_element.text
        if shop_name is None or len(shop_name) < 2:
            shop_names = shop_name_element.get_attribute('aria-label')
            if shop_names is not None and len(shop_names) > 1:
                shop_names = shop_names.split(' ')
                shop_name = shop_names[-1]
        if shop_name_element.is_displayed():
            is_ad = 0
        else:
            is_ad = 1

    # ad_text_elements = result.find_elements_by_xpath('.//div[contains(@class, "wt-text-caption")]/p[not(@aria-role) and contains(@class, "c439")]')

    
    try:
        star_ratings = result.find_element_by_xpath('.//input[@name="rating"]').get_attribute('value')
    except:
        star_ratings = np.nan
    
    try:
        num_review = result.find_element_by_xpath('.//span[contains(@class, "larger_review_stars")]/span[2]').text
        num_reviews = num_review.strip("()")
    except:
        num_reviews = 0
    
    try:
        prices = result.find_element_by_xpath('.//span[@class="currency-value"]').text
    except:
        prices = np.nan
        
    try:
        bestseller = np.nan
        bestsellers = result.find_elements_by_xpath('.//span[contains(text(), "estsell")]')
        if len(bestsellers) > 0:
            bestseller = 1

        popular_nows = result.find_elements_by_xpath('.//span[contains(text(), "opular")]')
        if len(popular_nows) > 0:
            bestseller = 2

        star_sellers = result.find_elements_by_xpath('.//p[contains(text(), "tar Seller")]')
        if len(star_sellers) > 0:
            bestseller = 3
    except:
        bestseller = np.nan
    
    category = term
    
    return titles, is_ad, shop_name, star_ratings, num_reviews, prices, bestseller, category

def next_page(driver, page_counter):
    """Clicks on the next page of search results. Takes the webdriver and current page_counter as arguments to ensure the right next page is located.  
    """
    try:
        xpath = '//ul[contains(@class, "search-pagination")]//a[contains(@href, "n&page={page_counter}") and contains(text(), "{page_counter}")]'.format(page_counter=page_counter)
        page = driver.find_element_by_xpath(xpath)
        next_page = page.get_attribute("href")
        
        for i in range(3): 
            try: 
              random_sleep_link = 4
              time.sleep(random_sleep_link)
              driver.get(next_page) 
            except requests.exceptions.RequestException:
              random_sleep_except = random.uniform(240,360)
              print("I've encountered an error! I'll pause for"+str(random_sleep_except/60) + " minutes and try again \n")
              time.sleep(random_sleep_except) 
              continue
            else: 
              break 
        else: 
            raise Exception("Something really went wrong here... I'm sorry.") 
    except:
        pass
    