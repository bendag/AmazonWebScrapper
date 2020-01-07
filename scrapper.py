import requests
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

import time
import re
import smtplib

### Email settings (use your own setting on your local repository) ###
from emailConfig import emailReceiver, emailSender, password

### item search settings ###
search = "water flosser"
maxPage = 1
minPrice = 15
maxPrice = 40

### create web driver ###
myProfileFirefox = webdriver.FirefoxProfile(
    "/home/bendag/.mozilla/firefox/ayeiszsd.webscrapper")
driver = webdriver.Firefox(firefox_profile=myProfileFirefox)
driver.get("https://www.amazon.ca/")

### fin search bar in website Amazon ###
elem = driver.find_element_by_xpath('//*[@id="twotabsearchtextbox"]')
elem.clear()
elem.send_keys(search)
elem.send_keys(Keys.RETURN)
assert "No results found." not in driver.page_source
time.sleep(1)
currentUrl = driver.current_url

### utils fonctions ###

# change page in amazon


def changePage():
    try:
        nextPage = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, '//*[@class="a-last"]'))
        )
        nextPage.find_element_by_tag_name('a')
        nextPage.click()
    except:
        print('module not find')

    return driver.current_url


# get name price and prev_price


def getData(url):
    url = "https://www.amazon.ca/dp/" + url
    driver.get(url)

    name = driver.find_element_by_id('productTitle').text
    try:
        price = driver.find_element_by_id('priceblock_ourprice').text
    except:
        price = -1
    try:
        prev_price = driver.find_element_by_xpath(
            '//*[@class="priceBlockStrikePriceString a-text-strike"]').text
        print("dicount found")
    except:
        prev_price = price

    product = {
        "name": name,
        "price": price,
        "prev_price": prev_price,
        "link": url,
        "discount": ""
    }
    return product


# get all products of x first pages

products = []
page = 1
index = 0

while(True):

    result = "//*[@data-index='" + str(index) + "']"

    try:
        item = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, result)))
        asin = item.get_attribute('data-asin')

        # add product to products list
        product = getData(asin)

        # only keep item with price and over 300$
        if(product["price"] != -1):
            products.append(product)

         # increment index
        index = index + 1

    except:
        print("page " + str(page) + " done")
        index = 0
        page = page + 1
        currentUrl = changePage()

   # terminal condition
    if(page > maxPage):
        break

    # revenir a la page precedente
    driver.get(currentUrl)


print("webDriver over")
driver.quit()


# change price into a number
def convertPrice():

    for i in range(len(products)):

        non_decimal = re.compile(r'[^\d.]+')
        products[i]["price"] = float(non_decimal.sub('', products[i]["price"]))
        products[i]["prev_price"] = float(non_decimal.sub(
            '', products[i]["prev_price"]))


# analysing data by biggest save


def biggestSave():
    for i in range(len(products)):
        price = products[i]["price"]
        prev_price = products[i]["prev_price"]

        discount = (prev_price - price) / prev_price
        products[i]["discount"] = discount

### parse data ###


def priceRange(minPrice=0, maxPrice=1000000):

    newList = []
    for item in range(len(products)):
        if(products[item]["price"] >= minPrice and products[item]["price"] <= maxPrice):
            newList.append(products[item])

    return newList


convertPrice()
biggestSave()
products = priceRange(minPrice=minPrice, maxPrice=maxPrice)

# Sort products from biggets discount to lower discount
products = sorted(
    products, key=lambda products: products['discount'], reverse=True)


### print results ###
for i in range(len(products)):
    print(products[i])

### sending email with best results ###


def send_mail():
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.ehlo()
    server.starttls()
    server.ehlo()

    server.login(emailSender, password)

    subject = f'5 biggest discount on {search} '
    body = f'Check the find items below \n\n \
            1. {products[0]["name"]}\n \
            link: {products[0]["link"]} \n\n \
            2. {products[1]["name"]}\n \
            link: {products[1]["link"]} \n\n \
            3. {products[2]["name"]}\n \
            link: {products[2]["link"]} \n\n \
            4. {products[3]["name"]}\n \
            link: {products[3]["link"]} \n\n \
            5. {products[4]["name"]}\n \
            link: {products[4]["link"]} \n\n'

    msg = f"Subject: {subject} \n\n{body}"

    server.sendmail(
        emailSender,
        emailReceiver,
        msg.encode("utf8")
    )
    print('Email sent')

    server.quit()


send_mail()
