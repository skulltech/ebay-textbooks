from ebaysdk.finding import Connection as Finding
from ebaysdk.shopping import Connection as Shopping
from ebaysdk.trading import Connection as Trading
from ebaysdk.exception import ConnectionError

import requests
import csv
import math
import sys

ID_APP = 'BarSowka-book-PRD-98dfd86bc-88e04dff'

finding_api = Finding(appid=ID_APP, config_file=None)
shopping_api = Shopping(appid=ID_APP, config_file=None)
trading_api = Trading(appid=ID_APP, config_file=None)

conditionsDict = {
    'Brand new': 1000,
    'Like new': 3000, 
    'Very Good': 4000, 
    'Good': 5000, 
    'Acceptable': 6000, 
}

listingTypes = ['Auction', 'AuctionWithBIN', 'Classified', 'FixedPrice', 'StoreInventory', 'All']
sortOrders = ['BestMatch', 'BidCountFewest', 'BidCountMost', 'CountryAscending', 'CountryDescending', 'CurrentPriceHighest', 'DistanceNearest', 'EndTimeSoonest', 'PricePlusShippingHighest', 'PricePlusShippingLowest', 'StartTimeNewest', 'WatchCountDecreaseSort']
conditionsList = ['Brand new', 'Like new', 'Very Good', 'Good', 'Acceptable']

def exitProgram(message):
    print(message or 'Exiting...')
    sys.exit()

def getProducts(keywords, page=1, entriesPerPage=100, sortOrder='BestMatch', condition='Brand new', listingType='All', options={}, freeShippingOnly=False, categoryID=267):

    if sortOrder   not in sortOrders:       exitProgram('Invalid sortOrder provided. Exiting...')
    if condition   not in conditionsList:   exitProgram('Invalid condition provided. Exiting...')
    if listingType not in listingTypes:     exitProgram('Invalid listingType provided. Exiting...')

    options['keywords'] = keywords
    options['paginationInput'] = {'entriesPerPage': entriesPerPage, 'pageNumber': page}
    options['sortOrder'] = sortOrder
    
    options['itemFilter'] = [
        {'name': 'MinPrice', 'value': 0, 'paramName': 'Currency', 'paramValue': 'USD'}, 
        {'name': 'MaxPrice', 'value': 100, 'paramName': 'Currency', 'paramValue': 'USD'}, 
        {'name': 'Condition', 'value': conditionsDict[condition]},
        {'name': 'ListingType', 'value': listingType},
        {'name': 'FreeShippingOnly', 'value': freeShippingOnly},
        {'name': 'HideDuplicateItems', 'value': True},
        {'name': 'categoryId', 'value': categoryID},
    ]

    response = finding_api.execute('findItemsAdvanced', options).dict()

    try:             ack = response['ack']
    except KeyError: exitProgram('Some unexpected error occurred! Check your connection. Exiting...')

    if ack != 'Success': exitProgram('Error returned from the API! Check your inputs. Exiting...')

    try:             result = response['searchResult']['item']
    except KeyError: exitProgram('No search results found! Exiting...')
    
    return result


def getISBN(ePID):

    payload = {
        'OPERATION-NAME': 'getProductDetails',
        'RESPONSE-DATA-FORMAT': 'JSON',
        'SECURITY-APPNAME': ID_APP,
        'SERVICE-VERSION': '1.3.0',
        'productDetailsRequest.productIdentifier.ePID': ePID,
        'productDetailsRequest.datasetPropertyName': 'ISBN'
    }

    response = requests.get("http://svcs.ebay.com/services/marketplacecatalog/ProductService/v1", params=payload)
    
    try:
        isbn = response.json()["getProductDetailsResponse"][0]["product"][0]["productDetails"][0]["value"][0]["text"][0]["value"][0]
    except KeyError:
        isbn = 'Not Available'    

    return isbn

def getPublicationYear(isbn):

    response = requests.get('https://www.googleapis.com/books/v1/volumes?q=isbn:{}'.format(isbn)).json()
    try:
        year = int(response['items'][0]['volumeInfo']['publishedDate'][:4])
    except KeyError:
        return 0
    else:
        return year


def getDesc(itemID):

    response = shopping_api.execute("GetSingleItem", {"ItemID": itemID, "IncludeSelector": "TextDescription"})    
    try:
        desc = response.dict()["Item"]["Description"]
    except KeyError:
        desc = 'Not Available'

    return desc


def filterData(products):
    filtered = []

    withoutProductID = 0
    withoutISBN = 0
    withoutDesc = 0
    oldProducts = 0
    
    for x in products:
        try:
            productId = x['productId']
        except KeyError:
            withoutProductID = withoutProductID + 1
        else:
            ref = productId['value']
            isbn = getISBN(ref)
            if isbn == 'Not Available':  
                withoutISBN = withoutISBN + 1
                continue
            
            link = 'http://www.ebay.com/itm/' + x['itemId']
            price = x['sellingStatus']['convertedCurrentPrice']['value']
            desc = getDesc(x['itemId'])

            if desc == 'Not Available':  withoutDesc = withoutDesc + 1

            publicationyear = getPublicationYear(isbn)
            if publicationyear < 2011:
                oldProducts = oldProducts + 1
                continue


            filtered.append({'ISBN': isbn, 'link': link, 'price': price, 'description': desc, 'publicationyear': publicationyear})

    print('Products without ProductID   : {}'.format(withoutProductID))
    print('Products without ISBN        : {}'.format(withoutISBN))
    print('Products without Description : {}'.format(withoutDesc))
    print('Products older than 2011     : {}'.format(oldProducts))


    return filtered

def main():

    n = int(input('Number of entries: '))
    keywords = input('Keywords: ')
    filename = input('Enter to filename of the output CSV file: ')
    products = []

    for page in range(1, math.ceil(n/100) + 1):
        print('Currently getting page no {}'.format(page))
        products = products + getProducts(keywords, page=page, entriesPerPage=n)
    
    print('Total number of items grabbed: {}'.format(len(products)))

    filteredProducts = filterData(products)

    with open(filename + '.csv', 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, filteredProducts[0].keys())
        w.writeheader()
        w.writerows(filteredProducts)
    
    f.close()

if __name__=='__main__':
    main()
    