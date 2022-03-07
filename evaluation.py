import os
import requests
import urllib.parse
import json
from datetime import datetime, timedelta, time
import pandas as pd
import yfinance as yf

from cs50 import SQL
from flask import redirect, render_template, request, session, jsonify
from functools import wraps

from helpers import apology, login_required, lookup, usd, eur, vnd, get_json, livePriceVN, historicalSSI, get_price_name, format_currency, percent
# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# assume startDate in string format
def get_historical(stock_list, market, startDate):
    # TODO: adjust symbol according to yfinance syntax
    for i in range(len(stock_list)):
        symbol_adj = ""
        for j in range(len(stock_list[i])):
            if stock_list[i][j] == ".":
                symbol_adj += "-"
            else:
                symbol_adj += stock_list[i][j]
        stock_list[i] = symbol_adj

    # convert startDate to date format
    startDate = datetime.strptime(startDate, '%Y-%m-%d')
    start = startDate - timedelta(days = 10)

    # TODO: prepare list of column names
    new_names = []
    for stock in stock_list:
        new_names.append(stock)

    # TODO: Update name in case of Germany market
    stock_list_new = []
    if market == "GR":
        # TODO: change ticker list
        for i in range(len(stock_list)):
            stock_list_new.append(stock_list[i] + ".DE")
    else:
        stock_list_new = stock_list

    if market == "US" or market == "GR":
        # TODO: get price time series
        stocks = ""
        columns = []
        for stock in stock_list_new:
            stocks += stock + " "
            if len(stock_list_new) > 1:
                columns.append(("Adj Close", stock))
            else:
                columns.append("Adj Close")

        # request data
        data = yf.download(stocks, start=start, end=datetime.now().strftime("%Y-%m-%d"))

        # TODO: update startDate, remove any observations before startDate, retain only relevant columns, rename those column
        while startDate not in data.index and startDate > data.index[0]:
            startDate = startDate - timedelta(days = 1)
        prior_dates_index = data.loc[data.index < startDate].index
        data.drop(prior_dates_index, inplace=True)
        data = data[columns]
        data.columns = new_names
        # formatting/standardizing output
        data.index = pd.to_datetime(data.index)
        data.index.name = 'time'
        return data
    else:
        data = None
        count = 0
        for stock in stock_list:
            # TODO: get price series in df format, changing column name to the respective ticker
            data_dict = get_json(stock, "VN")
            df = pd.DataFrame.from_dict(data_dict, orient="columns", dtype=None, columns=None)
            df.set_index("dateTime", drop=True, append=False, inplace=True, verify_integrity=False)
            df.rename(columns={"close": stock}, inplace=True)


            # TODO: clear the prior days
            while startDate not in df.index and startDate > df.index[0]:
                startDate = startDate - timedelta(days = 1)
            prior_dates_index = df.loc[df.index < startDate].index
            df.drop(prior_dates_index, inplace=True)
            if count == 0:
                data = df
                count += 1
            else:
                data = pd.merge(data, df, on="dateTime")
        data.index.name = 'time'
        return data

def map_priceSeries_transactions(user_id):
    tables = []
    stocks = db.execute("SELECT symbol, market FROM stocks WHERE stock_id IN (SELECT DISTINCT stock_id FROM transactions WHERE person_id=?)ORDER BY market, symbol", user_id)
    list_vn = []  #still useful
    list_us = []
    list_gr = []

    # get startDate in str format
    startDate_str = db.execute("SELECT startDate FROM users WHERE id=?", user_id)[0]["startDate"]
    startDate = datetime.strptime(startDate_str, "%Y-%m-%d %H:%M:%S").date().strftime('%Y-%m-%d')

    transactions_dict = db.execute(
        "SELECT * FROM stocks JOIN transactions ON stocks.stock_id=transactions.stock_id WHERE transactions.person_id=? ORDER BY market, symbol", user_id)
    for transaction in transactions_dict:
        trans_date = datetime.strptime(transaction["time"], "%Y-%m-%d %H:%M:%S").date()
        transaction["time"] = datetime.combine(trans_date, datetime.min.time())

    for stock in stocks:
        {"VN":list_vn, "US":list_us, "GR":list_gr}[stock["market"]].append(stock["symbol"])
    for market in ["VN", "US", "GR"]:
        stock_list = {"VN":list_vn, "US":list_us, "GR":list_gr}[market]
        if len(stock_list) == 0:
            #TODO
            df = yf.download("V", start=startDate, end=datetime.now().strftime("%Y-%m-%d"))
            cash_key = {"VN":"cash_vnd", "US":"cash_usd", "GR":"cash_eur"}[market]
            df["cash"] = db.execute("SELECT * FROM users WHERE id=?", user_id)[0][cash_key]
            df["transact_val_total"] = 0
            df["NAV"] = df["cash"]
            df = df[["cash", "transact_val_total", "NAV"]]
            df.index.name = 'time'
            tables.append(df)
        else:
            #TODO 1: Assume having a df of stock price time series
            stock_history = get_historical(stock_list, market, startDate)

            #TODO 2: Build df of transaction history
            for transaction in transactions_dict:
                # match transaction time with the nearest trading day no later than the actual date
                if transaction["market"] == market:
                    while transaction["time"] not in stock_history.index and transaction["time"] > stock_history.index[0]:
                        transaction["time"] = transaction["time"] - timedelta(days = 1)

            # convert transaction_dict to df format, add new column "value"
            df = pd.DataFrame.from_dict(transactions_dict, orient="columns", dtype=None, columns=None)
            df = df[["time", "market", "symbol", "transaction_price", "volume"]]
            df["value"] = df["transaction_price"] * df["volume"]
            df = df[["time", "market", "symbol", "volume", "value"]]  # scale down df to contain only necessary columns

            # scale down the df to the current market
            dfs = df.groupby(["market"])
            df = dfs.get_group(market)

            #TODO 3: transform df to individual stocks and merge them back to the stock_history df
            # sum up volume & value of each symbol each day, make (symbol+day) the columns
            dfs = df.groupby(["symbol", "time"]).sum()
            df = dfs.unstack(level=0)  # reshape the current df with stocks as columns

            #TODO 4: change column names to prepare for merging
            #columns = ""
            new_names = []
            for stock in stock_list:
                new_names.append(f"{stock}_volume")
            for stock in stock_list:
                new_names.append(f"{stock}_value")
            df.columns = new_names

            # Important: merge & clean
            df = pd.merge(stock_history, df, on="time", how = "outer")
            df = df.fillna(0)

            #TODO 5: Obtain portfolio values time series
            df["transact_val_net"] = 0
            df["transact_val_total"] = 0
            df["cash"] = 0
            for stock in stock_list:
                df[f"{stock}_no_shs"] = 0
                df["transact_val_net"] += df[f"{stock}_value"]

            for i in range(df.shape[0]):
                if i == 0:
                    df.loc[df.index[i], "cash"] = {"VN":100000, "US":10000, "GR":10000}[market] - df.loc[df.index[i], "transact_val_net"]
                    for stock in stock_list:
                        df.loc[df.index[i], f"{stock}_no_shs"] = df.loc[df.index[i], f"{stock}_volume"]
                else:
                    for stock in stock_list:
                        df.loc[df.index[i], "cash"] = df.loc[df.index[i - 1], "cash"] - df.loc[df.index[i], "transact_val_net"]
                        df.loc[df.index[i], f"{stock}_no_shs"] = df.loc[df.index[i - 1], f"{stock}_no_shs"] + df.loc[df.index[i], f"{stock}_volume"]

                # calculate total transaction value time series
                for stock in stock_list:
                    if df.loc[df.index[i], f"{stock}_value"] >= 0:
                        df.loc[df.index[i], "transact_val_total"] += df.loc[df.index[i], f"{stock}_value"]
                    else:
                        df.loc[df.index[i], "transact_val_total"] -= df.loc[df.index[i], f"{stock}_value"]

            df["NAV"] = df["cash"]
            for stock in stock_list:
                df["NAV"] += df[f"{stock}_no_shs"] * df[stock]

            df = df[["cash", "transact_val_total", "NAV"]]
            tables.append(df)
    return tables


def get_indexData(startDate, market):
    indices_list = {"VN":["HNX Index", "UpCom Index", "VN Index", "VN30 Index"], "US":["Dow Jones", "NASDAQ", "NYSE", "S&P 500"], "GR":["DAX", "HDAX"]}
    print(type(startDate))
    indexData_dict = db.execute("SELECT day, commonName, value FROM indices JOIN indexData ON indices.index_id = indexData.index_id WHERE indexMarket=? AND day>=?", market, startDate.date())
    for obs in indexData_dict:  
        obs_date = datetime.strptime(obs["day"], "%Y-%m-%d").date()
        obs["day"] = datetime.combine(obs_date, datetime.min.time())
    df = pd.DataFrame.from_dict(indexData_dict, orient="columns", dtype=None, columns=None)
    dfs = df.groupby(["commonName", "day"]).sum()  # update dfs accordingly
    df = dfs.unstack(level=0)
    df.columns = indices_list[market]
    df.index.name = 'time'
    return df


def get_Index_past10d_USGR():
    indices_list = {"^GSPC": 1, "^IXIC": 2, "^DJI": 3, "^NYA": 4, "^GDAXI": 5}
    symbols = ["^GSPC", "^IXIC", "^DJI", "^NYA", "^GDAXI"]
    start = (datetime.today() - timedelta(days = 30)).strftime('%Y-%m-%d')
    data = yf.download("^GSPC ^IXIC ^DJI ^NYA ^GDAXI", start=start, end=datetime.now().strftime("%Y-%m-%d"))
    data = data[[('Adj Close',   '^DJI'),
                ('Adj Close', '^GDAXI'),
                ('Adj Close',  '^GSPC'),
                ('Adj Close',  '^IXIC'),
                ('Adj Close',   '^NYA'),
                (   'Volume',   '^DJI'),
                (   'Volume', '^GDAXI'),
                (   'Volume',  '^GSPC'),
                (   'Volume',  '^IXIC'),
                (   'Volume',   '^NYA')]]
    for symbol in symbols:
        storage = db.execute("SELECT * FROM indexData WHERE index_id=? AND day>=?", indices_list[symbol], start)
        null_index = data.loc[data.loc[:, ("Adj Close", symbol)].isnull()].index
        for date in data.index:
            if date not in null_index:
                found = 0
                value_yf = float(data.loc[date, ("Adj Close", symbol)])
                volume_yf = int(data.loc[date, ("Volume", symbol)])
                for obs in storage:

                    if date == datetime.strptime(obs["day"], "%Y-%m-%d"):
                        if value_yf != obs["value"]:
                            db.execute("UPDATE indexData SET value=?, volume=? WHERE index_id=? AND day=?", value_yf, volume_yf, indices_list[symbol], obs["day"])
                        found = 1
                        break
                if found == 0:
                    db.execute("INSERT INTO indexData (index_id, day, value, volume) VALUES (?, ?, ?, ?)", indices_list[symbol], date.date(), value_yf, volume_yf)


def get_Index_past10d_VN():
    listVN = {"HNXUPCOMINDEX":10 , "VN30":9, "VNINDEX":8, "HNXINDEX":7}
    symbols = ["HNXUPCOMINDEX", "VN30", "VNINDEX", "HNXINDEX"]
    endDate = datetime.today().strftime('%Y-%m-%d')
    startDate = (datetime.today() - timedelta(days = 30)).strftime('%Y-%m-%d')
    for symbol in symbols:
        data = historicalSSI(symbol, startDate, endDate, "array")
        storage = db.execute("SELECT * FROM indexData WHERE index_id=? AND day>=?", listVN[symbol], startDate)
        for point in data:
            found = 0
            for obs in storage:
                if point["dateTime"] == datetime.strptime(obs["day"], "%Y-%m-%d"):
                    if  point["close"] != obs["value"]:
                        db.execute("UPDATE indexData SET value=?, volume=? WHERE index_id=? AND day=?", point["close"], point["volume"], listVN[symbol], obs["day"])
                    found = 1
                    break
            if found == 0:
                db.execute("INSERT INTO indexData (index_id, day, value, volume) VALUES (?, ?, ?, ?)", listVN[symbol], point["dateTime"].date(), point["close"], point["volume"])


def get_HDAX_past10d():
    session = requests.Session()
    # query data
    headers = {
        'Cookie': '_sp_v1_uid=1:846:67b1c41b-1c4e-4f52-99d4-4483d3cb54e6; _sp_krux=false; _sp_v1_lt=1:; _sp_v1_csv=null; gatehouse_id=832eaafe-afea-4062-ab2f-d694a135a757; bb_geo_info={"countryCode":"DE","country":"DE","field_n":"hf","trackingRegion":"Europe","cacheExpiredTime":1635168074489,"region":"Europe","fieldN":"hf"}|1635168074489; pxcts=44f6c700-3016-11ec-8b59-d32b336f4730; _pxvid=44f65022-3016-11ec-8ba8-475a6c646a76; _reg-csrf=s:AgdTDckTnqIOjIWR5fYzJYlr.ahMMJ2nSX7xNZ2rDj+GjFFNrIn5sfpYzReZqAnBU2M0; agent_id=c7abdb15-dd8d-48aa-866a-9dbb1024b83e; session_id=8434abdd-cdb1-4666-974b-c40158eb6771; session_key=6ec1dbe176bdd4d9dbe2af1ceacce94342cec20e; _user-status=anonymous; ccpaUUID=596b182f-d3e2-4684-beb9-608a8b0d90e4; ccpaApplies=true; dnsDisplayed=true; signedLspa=false; consentUUID=bc702a29-8955-4dce-85b1-cbce5db11a6d; _ga=GA1.2.1506527368.1635669313; _sp_v1_opt=1:login|true:last_id|12:; euconsent-v2=CPO71UYPO71UYAGABCENBzCgAAAAAAAAAAYgAAAAAAAA.YAAAAAAAAAAA; bbgconsentstring=req1fun0pad0; bdfpc=004.8154294925.1635669327099; _sp_v1_ss=1:H4sIAAAAAAAAAItWqo5RKimOUbLKK83J0YlRSkVil4AlqmtrlXQGVlk0kYw8EMOgNhaXkfSQwOZsfN4kySDKTBwUVsUCAMbru3FzAgAA; _sp_v1_consent=1!1:0:0:1:1:1; com.bloomberg.player.volume.level=1; bb_geo_info={"country":"DE","region":"Europe","fieldN":"hf"}|1638982932351; com.bloomberg.player.volume.muted=false; _parsely_visitor={"id":"pid=99d1ebdf079313b15d56ed88f8cefd7a","session_count":8,"last_session_ts":1641332752009}; PHPSESSID=rsk17lh16huq39hcn2siek11vb; professional-cookieConsent=required|performance|; professional-cPixel=required|performance|advertising|adwords|demandbase|linkedin-insights|media-shop|; _gcl_au=1.1.1947664406.1641344352; drift_aid=2cb80e08-008f-4f12-9a0b-1fafe1f129e4; driftt_aid=2cb80e08-008f-4f12-9a0b-1fafe1f129e4; geo_info={"countryCode":"DE","country":"DE","field_n":"hf","trackingRegion":"Europe","cacheExpiredTime":1642527871176,"region":"Europe","fieldN":"hf"}|1642527871176; geo_info={"country":"DE","region":"Europe","fieldN":"hf"}|1642527877669; _reg-csrf-token=pNIXQSRQ-L6zgJS6P60sWqKWfYlQz3TwNj8c; _sp_v1_data=2:392777:1634563273:0:28:0:28:0:0:_:-1; _pxff_rf=1; _pxff_fp=1; _px3=12359531904dcf0228bfb9dc452ea388e624248b2db8a6847dea1cc08cf0302a:1GnrbW4klin3SRt1g9xyOq4y+XGjNxDETYWnAJ1rBLi/0c475+PK543G5bmEz2Ia0b25GnfJBHiK8AglloTA+Q==:1000:vms6t9wMHTNHUOtRoIaK2Iqf0l3Xe1AZNfREaff3jsQ04MEyXL2GxoDDUILNzpRXu9naFMjVN0j1ssPA13qmL8LhMunBmUXQoA0QbVT2D28WfUfwKdmGLpurrU6MmMfLH32oGiloza1lrNV3tkmw8pn1WfchpHDqOYki9mVqdRmkwhuqnzG1oGWLXT0HQ7X1H0IUqCNO+phsdH+gcy88Pg==; _px2=eyJ1IjoiZjc4Yjg0NmEtNzkxNC0xMWVjLWE1ZDUtNTU0MjUwNjE3OTVhIiwidiI6IjQ0ZjY1MDIyLTMwMTYtMTFlYy04YmE4LTQ3NWE2YzY0NmE3NiIsInQiOjE2NDI1ODk0NjY5NDQsImgiOiIyOGE4YTk1ZjgwZTg5NjZjNzhmNjdiYTkwYzIwNTdlN2I2MThlNGQyZjljZDczYzcwZmZlNTA2YmMwYTY0ZWUwIn0=; _pxde=6ef069ad4b1d983ce685e592402c144dc295da44e96b0986f154915c8c13eb76:eyJ0aW1lc3RhbXAiOjE2NDI1ODkxNjY5MzIsImZfa2IiOjAsImlwY19pZCI6W119',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'
    }
    response = session.get(f"https://www.bloomberg.com/markets2/api/history/HDAX:IND/PX_LAST?timeframe=1_MONTH&period=daily&volumePeriod=daily", headers=headers)
    # Parse response
    quote = json.loads(response.text)
    data = []
    startDate = datetime.today() - timedelta(days = 30)
    for i in range(0, len(quote[0]["price"])):
        datePrice = datetime.strptime(quote[0]["price"][i]["dateTime"], '%Y-%m-%d')
        for j in range(0, len(quote[0]["volume"])):
            dateVolume = datetime.strptime(quote[0]["volume"][j]["dateTime"], '%Y-%m-%d')
            if datePrice == dateVolume and datePrice > startDate:
                close = quote[0]["price"][i]["value"]
                volume = quote[0]["volume"][j]["value"]
                data.append({"dateTime": datePrice, "close": close, "volume": volume})
                break
    storage = db.execute("SELECT * FROM indexData WHERE index_id=6 AND day>=?", startDate)
    for point in data:
        found = 0
        for obs in storage:
            if point["dateTime"] == datetime.strptime(obs["day"], "%Y-%m-%d"):
                if  point["close"] != obs["value"]:
                    db.execute("UPDATE indexData SET value=?, volume=? WHERE index_id=6 AND day=?", point["close"], point["volume"], obs["day"])
                found = 1
                break
        if found == 0:
            db.execute("INSERT INTO indexData (index_id, day, value, volume) VALUES (6, ?, ?, ?)", point["dateTime"].date(), point["close"], point["volume"])

