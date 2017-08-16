from ebaysdk.finding import Connection as Finding
from ebaysdk.shopping import Connection as Shopping
from ebaysdk.exception import ConnectionError

import requests
import csv
import math
import sys

ID_APP = 'BarSowka-book-PRD-98dfd86bc-88e04dff'

finding_api = Finding(appid=ID_APP, config_file=None)
shopping_api = Shopping(appid=ID_APP, config_file=None)

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

def getProducts(keywords, page=1, entriesPerPage=100, sortOrder='BestMatch', condition='Brand new', listingType='All', options={}, freeShippingOnly=False, categoryID=None):

    if sortOrder   not in sortOrders:   exitProgram('Invalid sortOrder provided. Exiting...')
    if condition   not in conditions:   exitProgram('Invalid condition provided. Exiting...')
    if listingType not in listingTypes: exitProgram('Invalid listingType provided. Exiting...')

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

    try:             result = response.dict()["searchResult"]["item"]
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
    isbn = response.json()["getProductDetailsResponse"][0]["product"][0]["productDetails"][0]["value"][0]["text"][0]["value"][0]    

    return response.json()


def getDesc(itemID):

    response = shopping_api.execute("GetSingleItem", {"ItemID": itemID, "IncludeSelector": "TextDescription"})    
    return response.dict()["Item"]["Description"]


def filterData(products):
    filtered = []
    
    for x in products:
        try:
            if x['productId']['_type'] != 'ReferenceID': 
                print('No refID found for item.')
            else:
                ref = x['productId']['value']
                isbn = getISBN(ref)
                link = 'http://www.ebay.com/itm/' + x['itemId']
                price = x['sellingStatus']['convertedCurrentPrice']['value']
                desc = getDesc(x['itemId']) or ''

                filtered.append({'ISBN': isbn, 'link': link, 'price': price, 'description': desc})
        except KeyError:
            print('Some data missing for item.')

def main():

    n = int(input('Number of entries: '))
    keywords = input('Keywords: ')
    filename = input('Enter to filename of the output CSV file: ')
    products = []

    for page in range(math.ceil(n/100) + 1):
        print('Currently getting page no {}'.format(page))
        products = products + getProducts(k, page, n, f)
    
    print('Total number of items grabbed: {}'.format(len(products)))

    filteredProducts = filterData(products)

    with open(filename + '.csv', 'w', encoding='utf-8') as f:
        w = csv.DictWriter(f, filteredProducts[0].keys())
        w.writeheader()
        w.writerows(filteredProducts)
    
    f.close()

if __name__=='__main__':
    main()
    