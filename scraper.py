from ebaysdk.finding import Connection as Finding
from ebaysdk.shopping import Connection as Shopping
from ebaysdk.exception import ConnectionError

import requests
import csv
import math

ID_APP = 'BarSowka-book-PRD-98dfd86bc-88e04dff'

finding_api = Finding(appid=ID_APP, config_file=None)
shopping_api = Shopping(appid=ID_APP, config_file=None)

conditions = {"brand new": "1000","like new": "2750","very good":"4000","good":"5000","acceptable":"6000"}

def getProducts(keywords, page, n=0, filter={}):
    entriesPerPage = 100 if n>100 else n
    keywords = keywords
    filtr["keywords"]=keywords
    filtr["paginationInput"]={"entriesPerPage": str(entriesPerPage), "pageNumber": str(page)}
    filtr["sortOrder"]="StartTimeNewest"
    #filtr["paginationOutput"]={"totalPages":pages,"totalEntries":str(n),"pageNumber": str(page),"entriesPerPage":"100"}
    response = finding_api.execute('findItemsByKeywords', filtr)
    try:
        x = response.dict()["searchResult"]["item"]
    except KeyError:
        x = []
    return x

def getISBN(ref):
    ref = str(ref)
    x = requests.get("http://svcs.ebay.com/services/marketplacecatalog/ProductService/v1?OPERATION-NAME=getProductDetails&RESPONSE-DATA-FORMAT=JSON&SECURITY-APPNAME="+ID_APP+"&SERVICE-VERSION=1.3.0&productDetailsRequest.productIdentifier.ePID="+ref+"&productDetailsRequest.datasetPropertyName=ISBN")
    return eval(x.content.decode("utf-8"))["getProductDetailsResponse"][0]["product"][0]["productDetails"][0]["value"][0]["text"][0]["value"][0]
    
    
def getDesc(itemID):
    itemID = str(itemID)
    response = shopping_api.execute("GetSingleItem", {"ItemID":itemID,"IncludeSelector":"TextDescription"})
    return response.dict()["Item"]["Description"]
n = int(input("n: "))
k = input("keywords: ")

f={"itemFilter":[
#{"name":"Condition", "value":conditions["brand new"]},
#{"name":"MaxPrice", "value":"10.00", "paramName":"Currency","paramValue":"USD"},
#{"name":"MinPrice", "value":"5.00", "paramName":"Currency","paramValue":"USD"},
#{"name":"ListingType", "value":"FixedPrice"}
]}
t = [] #getProducts(k,n,f)
for page in range(int(input("start page: ")),math.ceil(n/100)+1):
    print(page)
    temp = getProducts(k,page,n,f)
    t = t+ temp
print(len(t))

t2 = []
for x in t:
    try:
        if x["productId"]["_type"] == "ReferenceID":
            #print("refID found !!!!")
            ref = x["productId"]["value"]
            isbn = getISBN(ref)
            link = "http://www.ebay.com/itm/"+x["itemId"]
            price = x["sellingStatus"]["convertedCurrentPrice"]["value"]
            #desc = getDesc(x["itemId"]) or ""
            t2.append({"ISBN": isbn, "link": link, "price": price})#, "description": desc})
    except KeyError:
        pass

with open(str(input("filename: "))+".csv", "w",encoding="utf-8") as f:
    w = csv.DictWriter(f, t2[0].keys())
    w.writeheader()
    w.writerows(t2)
f.close()
