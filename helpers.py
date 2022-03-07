import os
import requests
import urllib.parse
import json

from datetime import datetime
from cs50 import SQL
from flask import redirect, render_template, request, session, jsonify
from functools import wraps
import pandas as pd
import yfinance as yf

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.
    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def yfinance_json(symbol, market, start, end, period):
    # TODO: adjust symbol according to yfinance syntax
    symbol_adj = ""
    for i in range(len(symbol)):
        if symbol[i] == ".":
            symbol_adj += "-"
        else:
            symbol_adj += symbol[i]
    symbol = symbol_adj
    if market == "GR":
        symbol = symbol + ".DE"
    # set symbol object & obtain data
    ticker = yf.Ticker(symbol)
    if period != "":
        df = ticker.history(period=period, interval="1d")
    else:
        df = ticker.history(start=start, end=end, interval="1d")
    if df.shape[0] != 0:
        dates = df.index
        close = df.iloc[:, 3]
        data = []
        for i in range(df.shape[0]):
            data.append({"dateTime":dates[i].date(), "close":round(close[i], 3)})
        return data
    else:
        return None

def historicalSSI(symbol, startDate, endDate, output_format):
    symbol = symbol.upper()
    if startDate != "":
        startDate = datetime.strptime(startDate, "%Y-%m-%d").date()
        start = datetime.combine(startDate, datetime.min.time()).timestamp()
        endDate = datetime.strptime(endDate, "%Y-%m-%d").date()
        end = datetime.combine(endDate, datetime.min.time()).timestamp()
        period = f"&from={start}&to={end}"
    else:
        period = ""
    response = requests.get(f"https://iboard.ssi.com.vn/dchart/api/history?resolution=D&symbol={symbol}{period}")
    try:
        data = json.loads(response.text)
        if len(data["t"]) == 0:
            return None
        data_dict = []
        for i in range(len(data["t"])):
            dateTime = datetime.fromtimestamp(data["t"][i])
            close = float(data["c"][i])
            volume = int(data["v"][i])
            data_dict.append({"dateTime":dateTime, "close":close, "volume":volume})
        if output_format == "array":
            return data_dict
        if output_format == "df":
            df = pd.DataFrame.from_dict(data_dict, orient="columns", dtype=None, columns=None)
            return df
    except (KeyError, TypeError, ValueError):
        return None


def bbg_json(symbol, market):
    session = requests.Session()
    market = ':' + market
    # fix link
    symbol_link = ''
    for i in range(0, len(symbol)):
        if symbol[i] == '.':
            symbol_link = symbol_link + '/'
        else:
            symbol_link = symbol_link + symbol[i]
    # query data
    headers = {
        'Cookie': '_sp_v1_uid=1:846:67b1c41b-1c4e-4f52-99d4-4483d3cb54e6; _sp_krux=false; _sp_v1_lt=1:; _sp_v1_csv=null; gatehouse_id=832eaafe-afea-4062-ab2f-d694a135a757; bb_geo_info={"countryCode":"DE","country":"DE","field_n":"hf","trackingRegion":"Europe","cacheExpiredTime":1635168074489,"region":"Europe","fieldN":"hf"}|1635168074489; pxcts=44f6c700-3016-11ec-8b59-d32b336f4730; _pxvid=44f65022-3016-11ec-8ba8-475a6c646a76; _reg-csrf=s:AgdTDckTnqIOjIWR5fYzJYlr.ahMMJ2nSX7xNZ2rDj+GjFFNrIn5sfpYzReZqAnBU2M0; agent_id=c7abdb15-dd8d-48aa-866a-9dbb1024b83e; session_id=8434abdd-cdb1-4666-974b-c40158eb6771; session_key=6ec1dbe176bdd4d9dbe2af1ceacce94342cec20e; _user-status=anonymous; ccpaUUID=596b182f-d3e2-4684-beb9-608a8b0d90e4; ccpaApplies=true; dnsDisplayed=true; signedLspa=false; consentUUID=bc702a29-8955-4dce-85b1-cbce5db11a6d; _ga=GA1.2.1506527368.1635669313; _sp_v1_opt=1:login|true:last_id|12:; euconsent-v2=CPO71UYPO71UYAGABCENBzCgAAAAAAAAAAYgAAAAAAAA.YAAAAAAAAAAA; bbgconsentstring=req1fun0pad0; bdfpc=004.8154294925.1635669327099; _sp_v1_ss=1:H4sIAAAAAAAAAItWqo5RKimOUbLKK83J0YlRSkVil4AlqmtrlXQGVlk0kYw8EMOgNhaXkfSQwOZsfN4kySDKTBwUVsUCAMbru3FzAgAA; _sp_v1_consent=1!1:0:0:1:1:1; com.bloomberg.player.volume.level=1; bb_geo_info={"country":"DE","region":"Europe","fieldN":"hf"}|1638982932351; com.bloomberg.player.volume.muted=false; _parsely_visitor={"id":"pid=99d1ebdf079313b15d56ed88f8cefd7a","session_count":8,"last_session_ts":1641332752009}; PHPSESSID=rsk17lh16huq39hcn2siek11vb; professional-cookieConsent=required|performance|; professional-cPixel=required|performance|advertising|adwords|demandbase|linkedin-insights|media-shop|; _gcl_au=1.1.1947664406.1641344352; drift_aid=2cb80e08-008f-4f12-9a0b-1fafe1f129e4; driftt_aid=2cb80e08-008f-4f12-9a0b-1fafe1f129e4; geo_info={"countryCode":"DE","country":"DE","field_n":"hf","trackingRegion":"Europe","cacheExpiredTime":1642527871176,"region":"Europe","fieldN":"hf"}|1642527871176; geo_info={"country":"DE","region":"Europe","fieldN":"hf"}|1642527877669; _reg-csrf-token=pNIXQSRQ-L6zgJS6P60sWqKWfYlQz3TwNj8c; _sp_v1_data=2:392777:1634563273:0:28:0:28:0:0:_:-1; _pxff_rf=1; _pxff_fp=1; _px3=12359531904dcf0228bfb9dc452ea388e624248b2db8a6847dea1cc08cf0302a:1GnrbW4klin3SRt1g9xyOq4y+XGjNxDETYWnAJ1rBLi/0c475+PK543G5bmEz2Ia0b25GnfJBHiK8AglloTA+Q==:1000:vms6t9wMHTNHUOtRoIaK2Iqf0l3Xe1AZNfREaff3jsQ04MEyXL2GxoDDUILNzpRXu9naFMjVN0j1ssPA13qmL8LhMunBmUXQoA0QbVT2D28WfUfwKdmGLpurrU6MmMfLH32oGiloza1lrNV3tkmw8pn1WfchpHDqOYki9mVqdRmkwhuqnzG1oGWLXT0HQ7X1H0IUqCNO+phsdH+gcy88Pg==; _px2=eyJ1IjoiZjc4Yjg0NmEtNzkxNC0xMWVjLWE1ZDUtNTU0MjUwNjE3OTVhIiwidiI6IjQ0ZjY1MDIyLTMwMTYtMTFlYy04YmE4LTQ3NWE2YzY0NmE3NiIsInQiOjE2NDI1ODk0NjY5NDQsImgiOiIyOGE4YTk1ZjgwZTg5NjZjNzhmNjdiYTkwYzIwNTdlN2I2MThlNGQyZjljZDczYzcwZmZlNTA2YmMwYTY0ZWUwIn0=; _pxde=6ef069ad4b1d983ce685e592402c144dc295da44e96b0986f154915c8c13eb76:eyJ0aW1lc3RhbXAiOjE2NDI1ODkxNjY5MzIsImZfa2IiOjAsImlwY19pZCI6W119',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'
    }
    response = session.get(f"https://www.bloomberg.com/markets2/api/history/{urllib.parse.quote_plus(symbol_link)}{urllib.parse.quote_plus(market)}/PX_LAST?timeframe=5_YEAR&period=daily", headers=headers)
    # Parse response
    try:
        quote = json.loads(response.text)
        data = []
        for i in range(0, len(quote[0]["price"])):
            data.append({"dateTime" : datetime.strptime(quote[0]["price"][i]["dateTime"], '%Y-%m-%d'), "close" : quote[0]["price"][i]["value"]})
        return data
    except (KeyError, TypeError, ValueError):
        return None


def get_json(symbol, market):
    if market == "US" or market == "GR":
        yf_data = yfinance_json(symbol, market, "", "", "max")
        if yf_data != None:
            return yf_data
        else:
            bbg_data = bbg_json(symbol, market)
            if bbg_data != None:
                return bbg_data
            else:
                return None
    else:
        data = historicalSSI(symbol, "", "", "array")
        if data != None:
            return data
        response = requests.get(f"https://s.cafef.vn/ajax/bieudokythuat.ashx?symbol={symbol}")
        try:
            jsonData = response.content.decode("utf-8").split(';')[1]
            quote_text = ''
            for i in range(0, len(jsonData)):
                if jsonData[i] == '[':
                    for j in range(i, len(jsonData)):
                        quote_text += jsonData[j]
                    break
            quote = json.loads(quote_text)

            data = []
            # change key name in json dictionary
            for i in range(0, len(quote)):
                quote[i]["dateVN"] = datetime.strptime(quote[i]["dateVN"], '%d/%m/%Y')
                data.append({"dateTime" : quote[i]["dateVN"], "close" : quote[i]["close"]})
            return data
        except (KeyError, TypeError, ValueError):
            return None

def lookup(symbol, market):
    """Look up quote for symbol."""
    #TODO: make sure symbol exist on yfinance first
    if not yfinance_json(symbol, market, "", "", "5d"):
        return None

    # adjust market to the API link
    mkt_link = ""
    if market == 'GR':
        mkt_link = '-GY'
    # Contact API
    try:
        api_key = "pk_e04ac775550746dca2e065f26e1b4e01" #os.environ.get("API_KEY")
        url = f"https://cloud.iexapis.com/stable/stock/{urllib.parse.quote_plus(symbol)}{mkt_link}/quote?token={api_key}"
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException:
        return None

    # Parse response
    try:
        quote = response.json()
        return {
            "name": quote["companyName"],
            "price": float(quote["latestPrice"]),
            "symbol": quote["symbol"]
        }
    except (KeyError, TypeError, ValueError):
        return None


def queryPriceSSI(exchange):
    payload = {
      'operationName':'stockRealtimes',
      'query':'query stockRealtimes($exchange: String) {\n  stockRealtimes(exchange: $exchange) {\n    stockNo\n    ceiling\n    floor\n    refPrice\n    stockSymbol\n    stockType\n    exchange\n    matchedPrice\n    matchedVolume\n    priceChange\n    priceChangePercent\n    highest\n    avgPrice\n    lowest\n    nmTotalTradedQty\n    best1Bid\n    best1BidVol\n    best2Bid\n    best2BidVol\n    best3Bid\n    best3BidVol\n    best4Bid\n    best4BidVol\n    best5Bid\n    best5BidVol\n    best6Bid\n    best6BidVol\n    best7Bid\n    best7BidVol\n    best8Bid\n    best8BidVol\n    best9Bid\n    best9BidVol\n    best10Bid\n    best10BidVol\n    best1Offer\n    best1OfferVol\n    best2Offer\n    best2OfferVol\n    best3Offer\n    best3OfferVol\n    best4Offer\n    best4OfferVol\n    best5Offer\n    best5OfferVol\n    best6Offer\n    best6OfferVol\n    best7Offer\n    best7OfferVol\n    best8Offer\n    best8OfferVol\n    best9Offer\n    best9OfferVol\n    best10Offer\n    best10OfferVol\n    buyForeignQtty\n    buyForeignValue\n    sellForeignQtty\n    sellForeignValue\n    caStatus\n    tradingStatus\n    currentBidQty\n    currentOfferQty\n    remainForeignQtty\n    session\n    __typename\n  }\n}\n',
      'variables':'{"exchange":"' + exchange + '"}'
    }
    response = requests.post('https://wgateway-iboard.ssi.com.vn/graphql', payload)
    try:
        result_dict = response.content.decode("utf-8")
        result = json.loads(result_dict)["data"]["stockRealtimes"]
        return result
    except (KeyError, TypeError, ValueError):
        print("queryPriceSSI(exchange) not work")
        return None


def queryPriceVDS(exchange):
    session = requests.Session()
    if exchange == 'hose':
        exchange = 'hsx'
    link = f"https://livedragon.vdsc.com.vn/{exchange}/{exchange}Init.rv"

    # send 1st request to get cookies
    headers = {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36',
        }
    session.get(link, headers=headers)

    #send 2nd request to get data
    response = session.get(link, headers=headers, cookies = {'langIdCkName':'en_US'})
    try:
        result_dict = response.content.decode("utf-8")
        result = json.loads(result_dict)
        price = result["grids"]
        symbol = result["stocks"]
        output = []

        # append data to output
        for i in range(len(symbol)):
            if price[i][11][0] == '&nbsp;':
                livePrice = price[i][0][0]
            else:
                livePrice = price[i][11][0]
            output.append({'stockSymbol':symbol[i][0], 'matchedPrice':float(livePrice)})
        return result
    except (KeyError, TypeError, ValueError):
        print("queryPriceVDS(exchange) not work")
        return None


def livePriceVN(symbol, symbols):  # symbol: single stock, symbols: array of stocks
    for exchange in ['hose', 'hnx', 'upcom']:
        result = queryPriceSSI(exchange)
        if result != None:
            if symbol != "":
                for i in range(len(result)):
                    dataPoint = result[i]
                    if symbol == dataPoint["stockSymbol"]:
                        if dataPoint["matchedPrice"] == None or dataPoint["matchedPrice"] == 0:  # if data on SSI is cleared for new session, get it from cafef
                            if dataPoint["refPrice"] == None or dataPoint["refPrice"] == 0:
                                json = get_json(symbol, 'VN')
                                return json[len(json) - 1]["close"]
                            else:
                                return dataPoint["refPrice"]/1000
                        else:
                            return dataPoint["matchedPrice"]/1000
            else:
                prices, tickers = [], []
                for ticker in symbols:
                    for i in range(len(result)):
                        dataPoint = result[i]
                        if ticker == dataPoint["stockSymbol"]:
                            if dataPoint["matchedPrice"] == None or dataPoint["matchedPrice"] == 0:  # if data on SSI is cleared for new session, get it from cafef
                                if dataPoint["refPrice"] == None or dataPoint["refPrice"] == 0:
                                    json = get_json(symbol, 'VN')
                                    prices.append(json[len(json) - 1]["close"])
                                    tickers.append(ticker)
                                else:
                                    prices.append(dataPoint["refPrice"]/1000)
                                    tickers.append(ticker)
                            else:
                                prices.append(dataPoint["matchedPrice"]/1000)
                                tickers.append(ticker)
                if len(tickers) == len(symbols):
                    return [tickers, prices]
    if symbol == "":
        return [tickers, prices]
    else:
        return None


def getNameVN():
    response = requests.get("https://iboard.ssi.com.vn/dchart/api/1.1/defaultAllStocks")
    try:
        result_dict = response.content.decode("utf-8")
        result = json.loads(result_dict)["data"]
        data = []
        for i in range(len(result)):
            dataPoint = result[i]
            data.append({'symbol':dataPoint["name"], 'name':dataPoint["clientNameEn"]})
        return data
    except (KeyError, TypeError, ValueError):
        print("getNameVN() not work")
        return None


def get_price_name(symbol, market):
    if market == 'US' or market == 'GR':
        result = lookup(symbol, market)
        if result == None:
            return None
        else:
            name = result["name"]
            if market == 'US':
                price = result["price"]
            else:
                json = get_json(symbol, market)
                price = json[len(json) - 1]["close"]

    if market == 'VN':
        price = livePriceVN(symbol, [])  # get live price
        if price == None:
            return None
        # look for symbol in database first
        DBquery = db.execute("SELECT companyname FROM stocks WHERE market='VN' AND symbol=?", symbol)
        if len(DBquery) == 1:
            name = DBquery[0]["companyname"]

        else:  # if symbol not in database, query live
            nameList = getNameVN()
            available = False
            for i in range(len(nameList)):
                if symbol == nameList[i]['symbol']:
                    name = nameList[i]['name']
                    available = True
                    break

            # if symbol is also not available online, return None
            if available == False:
                return None

    # if there is no problem, return price and company name
    return {'price':price, 'name':name}


def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"


def eur(value):
    """Format value as EUR."""
    return f"€{value:,.2f}"


def vnd(value):
    """Format value as VND."""
    value = value * 1000
    return f"VND {value:,.0f}"


def format_currency(value, market):
    if market == 'US':
        return usd(value)
    if market == 'GR':
        return eur(value)
    if market == 'VN':
        return vnd(value)
    else:
        return None


def percent(value):
    if value > 0:
        return f"+{value:,.2f}%"
    else:
        return f"{value:,.2f}%"