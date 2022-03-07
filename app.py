import os
from datetime import datetime
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, send_from_directory, current_app, jsonify
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
import pandas as pd

from helpers import apology, login_required, lookup, usd, eur, vnd, get_json, livePriceVN, get_price_name, format_currency, percent, yfinance_json
from evaluation import get_historical, map_priceSeries_transactions, get_indexData, get_Index_past10d_USGR, get_Index_past10d_VN, get_HDAX_past10d

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
#app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
#if not os.environ.get("API_KEY"):
#    raise RuntimeError("API_KEY not set")


@app.route("/")
#@login_required
def index():
    return render_template("about-trade-evaluation.html")

@app.route("/1")
#@login_required
def index1():
    name = "Annonymous"
    email = "None"
    subject = "None"
    message = "New access see Homepage"
    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    mess = db.execute("INSERT INTO messages VALUES (?, ?, ?, ?, ?)", time, 2, email, message, name)
    return redirect("/")

special_message = [""]
@app.route("/trade", methods=["GET", "POST"])
@login_required
def buy():
    """Buy/Sell layout"""
    if request.method == "GET":
        stock_list = db.execute(
            "SELECT * FROM stocks WHERE stock_id IN (SELECT stock_id FROM portfolios WHERE person_id=?)", session["user_id"])
        global special_message
        return render_template("trade.html", stock_list=stock_list, special_message=special_message)
    elif request.method == "POST":
        if session["user_id"] == 4:
            return apology("sorry, this account is only for demonstration purpose. create an account to make your own transactions")
        if not request.form.get("symbol"):
            return apology("stock is missing")
        elif not request.form.get("shares"):
            return apology("number of shares is missing")
        elif not request.form.get("market"):
            return apology("market is missing")
        elif request.form.get("market").upper() not in ['US', 'GR', 'VN']:
            return apology("market not supported yet")
        else:
            # check for valid volume
            volume_str = request.form.get("shares")
            check = [int(s) for s in volume_str.split() if s.isdigit()]
            if len(check) != 1 or int(volume_str) < 0:
                return apology("invalid number of shares")
            else:
                volume = int(volume_str)

            # check for valid combination of symbol and market
            symbol = request.form.get("symbol").upper()
            market = request.form.get("market").upper()
            search = get_price_name(symbol, market)
            if search == None:
                return apology("invalid symbol")
            else:
                price = search["price"]
                name = search["name"]
                value = price * volume

                # debit cash balance
                cash_key = {'US':'cash_usd', 'VN':'cash_vnd', 'GR':'cash_eur'}[market]
                command = f"SELECT {cash_key} FROM users WHERE id=?"
                cash = db.execute(command, session["user_id"])[0][cash_key]
                if value > cash:
                    return apology("Not enough cash")  # no transaction achieved
                else:
                    cash_remain = cash - value
                    command = f"UPDATE users SET {cash_key}=? WHERE id=?"
                    db.execute(command, cash_remain, session["user_id"])
                    stock_id = db.execute("SELECT stock_id FROM stocks WHERE symbol=? AND market=?", symbol, market)
                    if not stock_id:  # if stock not yet in database
                        # add new stock to the stocks table
                        db.execute("INSERT INTO stocks (symbol, companyname, price, market) VALUES (?, ?, ?, ?)",
                                   symbol, name, price, market)
                        # add new holding to the portfolios table
                        # select stock_id from stocks table
                        stock_id = db.execute("SELECT stock_id FROM stocks WHERE symbol=? AND market=?", symbol, market)
                        # add stock to portfolios table
                        total = price * volume
                        db.execute("INSERT INTO portfolios VALUES (?, ?, ?, ?, ?)", session["user_id"],
                                   stock_id[0]["stock_id"], volume, total, price)
                    else:
                        # check if user already own that stock
                        stock_in_port = db.execute("SELECT * FROM portfolios WHERE stock_id=? AND person_id=?",
                                                   stock_id[0]["stock_id"], session["user_id"])
                        if not stock_in_port:
                            # if not, insert the new holding to portfilios table
                            total = price * volume
                            db.execute("INSERT INTO portfolios VALUES (?, ?, ?, ?, ?)",
                                       session["user_id"], stock_id[0]["stock_id"], volume, total, price)
                        else:
                            # if yes, just update the number of shares and the total position on that stock
                            no_shs = stock_in_port[0]["no_shs"] + volume
                            cost_price = (stock_in_port[0]["cost_price"] * stock_in_port[0]["no_shs"] + price * volume) / no_shs
                            total = price * no_shs
                            db.execute("UPDATE portfolios SET no_shs=? WHERE person_id=? AND stock_id=?",
                                       no_shs, session["user_id"], stock_id[0]["stock_id"])
                            db.execute("UPDATE portfolios SET total=? WHERE person_id=? AND stock_id=?",
                                       total, session["user_id"], stock_id[0]["stock_id"])
                            db.execute("UPDATE portfolios SET cost_price=? WHERE person_id=? AND stock_id=?",
                                       cost_price, session["user_id"], stock_id[0]["stock_id"])
                    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    db.execute("INSERT INTO transactions (person_id, transaction_price, volume, time, stock_id) VALUES (?, ?, ?, ?, ?)",
                               session["user_id"], price, volume, time, stock_id[0]["stock_id"])

                return redirect("/")


last_update = datetime.strptime("2022-02-22", "%Y-%m-%d").date()
@app.route("/history")
@login_required
def history():
    global last_update
    print(last_update)
    if datetime.today().date() != last_update:
        get_Index_past10d_USGR()
        get_Index_past10d_VN()
        get_HDAX_past10d()
        last_update = datetime.today().date()
    
    name = "Annonymous"
    email = "None"
    subject = "None"
    message = "Most recent data update"
    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    mess = db.execute("INSERT INTO messages VALUES (?, ?, ?, ?, ?)", time, 3, email, message, name)
    
    """Show history of transactions"""
    transactions = db.execute("SELECT * FROM transactions JOIN stocks ON transactions.stock_id = stocks.stock_id WHERE person_id=? ORDER BY time", session["user_id"])
    return render_template("history.html", transactions=transactions)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/quote")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        global special_message
        #special_message = ["A simple primary alert with ", "an example link", ". Give it a click if you like.", "facebook.com"]
        return render_template("login.html", special_message=special_message)


@app.route("/communicate", methods=["GET", "POST"])
def communicate():
    """Display announcement (e.g. system maintenance/update)"""

    

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
#login_required
def quote():
    """Get stock quote."""
    if request.method == "GET":
        return render_template("quote.html")
    else:
        # get info from the form and check for validity
        symbol = request.form.get("symbol")
        market = request.form.get("market")
        if not symbol:
            return apology("no symbol")
        if not market:
            return apology("no market")
        if market not in ['us', 'vn', 'gr']:
            return apology("market not supported")
        symbol = symbol.upper()
        market = market.upper()

        # check if the symbol is correct and then return the most recent price
        if market == 'US' or market == 'GR':
            # look for company information and current stock price
            result = lookup(symbol, market)
            if result == None:
                return apology("symbol not exist")
            else:
                json = get_json(symbol, market)
                if json != None:
                    price_unformatted = json[len(json) - 1]["close"]
                    if market == 'US':
                        price = usd(result["price"])
                    else:
                        price = eur(price_unformatted)
                    return render_template("quoted.html", name=result["name"], symbol=symbol, price=price, market=market, data=json, message="")
                else:
                    price = format_currency(result["price"], market)
                    message = "Historical price data unavailable."
                    return render_template("quoted.html", name=result["name"], symbol=symbol, price=price, market=market, data=json, message=message)

        elif market == 'VN':
            name = "N/A"
            names = db.execute('SELECT companyname FROM stocks WHERE symbol=? AND market="VN"', symbol)
            if len(names)  == 1:
                name = names[0]["companyname"]
            price_unformatted = livePriceVN(symbol, [])
            if price_unformatted == None:
                return apology("symbol not exist")
            else:
                price = vnd(price_unformatted)
                json = get_json(symbol, market)
                return render_template("quoted.html", name=name, symbol=symbol, price=price, market=market, data=json)
        else:
            return apology("invalid market")


@app.route('/js/<path:filename>')
def send_js(filename):
    path = os.path.join(current_app.root_path, "js/")
    return send_from_directory(path, filename, as_attachment=True)    


@app.route('/portfolio', methods=["POST", "GET"])  # return time series of stock price for Quote page
@login_required
def send_port():
    if request.method == "GET":
        return render_template("index.html")
    elif request.method == "POST":
        # init global var
        markets = ['US', 'VN','GR']
        cash_list = ['cash_usd', 'cash_vnd', 'cash_eur']
        port_init = [10000, 100000, 10000]
        json = {}

        # update prices
        stocks = db.execute(
            "SELECT symbol, market FROM stocks WHERE stock_id IN (SELECT stock_id FROM portfolios WHERE person_id=?)", session["user_id"])
        symbolsVN = []
        for stock in stocks:
            if stock["market"] != "VN":
                price_name = get_price_name(stock["symbol"], stock["market"])
                if price_name != None:
                    price = price_name["price"]
                    db.execute("UPDATE stocks SET price=? WHERE symbol=? AND market=?", float(price), stock["symbol"], stock["market"])
            else:
                symbolsVN.append(stock["symbol"])
        if len(symbolsVN) > 0:
            data = livePriceVN("", symbolsVN)
            for i in range(len(data[0])):
                db.execute("UPDATE stocks SET price=? WHERE symbol=? AND market='VN'", data[1][i], data[0][i])

        """Show portfolio of stocks"""
        # loop through 3 markets
        for i in range(3):
            json[markets[i]] = {}  # init dict of stocks in each market
            json[markets[i]]["stocks"] = []

            # query cash data
            command = f"SELECT {cash_list[i]} FROM users WHERE id=?"
            cash_dict_format = db.execute(command, session["user_id"])
            cash_unformatted = cash_dict_format[0][cash_list[i]]
            cash = format_currency(cash_unformatted, markets[i])

            # update cash data to json #
            json[markets[i]]['cash'] = cash

            # revise stock prices and portfilio values
            port_value = cash_unformatted  # initializing port value with cash balance

            # query portfolio data, keep in mind that prices have been updated above but not total
            portfolio = db.execute(
                "SELECT * FROM portfolios JOIN stocks ON stocks.stock_id = portfolios.stock_id WHERE person_id=? AND market=? ORDER BY stocks.symbol", session["user_id"], markets[i])
            for stock in portfolio:

                # query prices, which have been updated above AND use them to calculate total holdings
                price = db.execute("SELECT * FROM stocks WHERE stock_id=?", stock["stock_id"])[0]["price"]
                total = price * stock["no_shs"]
                gl = percent(((price / stock["cost_price"]) - 1) * 100)

                # revise AND format the data in the portfolio variable too...
                stock["total"] = format_currency(total, markets[i])
                stock["price"] = format_currency(price, markets[i])
                stock["cost_price"] = format_currency(stock["cost_price"], markets[i])

                # add stock info to json
                json[markets[i]]['stocks'].append({
                    'symbol':stock["symbol"], 'companyname':stock["companyname"], 'no_shs':stock["no_shs"], 'current_price':stock["price"], 'cost_price':stock["cost_price"], 'total':stock["total"], '%g/l': gl})
                # ...and update total to portfolios table
                db.execute("UPDATE portfolios SET total=? WHERE stock_id=? AND person_id=?", total, stock["stock_id"], session["user_id"])

                # increase port value count
                port_value += total

            portGL = percent((port_value / port_init[i] - 1) * 100)
            # update port value to json
            json[markets[i]]['portVal'] = format_currency(port_value, markets[i])
            json[markets[i]]['portGL'] = portGL
        return jsonify(json)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        email = request.form.get("email")
        confirmation = request.form.get("confirmation")

        # check if username and password are typed in
        if not username:
            return apology("no username")
        elif not password:
            return apology("no password")
        elif not email:
            return apology("no email")

        #
        if password != confirmation:
            return apology("Password mismatched")
        else:
            users = db.execute("SELECT * FROM users WHERE username = ?", username)
            if len(users) != 0:
                return apology("Invalid Username")
            else:
                pwd = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)
                startDate = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                db.execute("INSERT INTO users (username, hash, email, startDate) VALUES(?, ?, ?, ?)", username, pwd, email, startDate)
                return redirect("/")
    if request.method == "GET":
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "GET":
        stock_list = db.execute(
            "SELECT * FROM stocks WHERE stock_id IN (SELECT stock_id FROM portfolios WHERE person_id=?)", session["user_id"])
        return render_template("sell.html", stock_list=stock_list)
    elif request.method == "POST":
        if session["user_id"] == 4:
            return apology("sorry, this account is only for demonstration purpose. create an account to make your own transactions")
        if not request.form.get("shares"):
            return apology("number of shares is missing")
        elif not request.form.get("symbol"):
            return apology("no stock selected")
        elif not request.form.get("market"):
            return apology("no market selected")
        else:
            symbol = request.form.get("symbol")
            market = request.form.get("market").upper()
            stock = db.execute("SELECT * FROM stocks JOIN portfolios on stocks.stock_id = portfolios.stock_id WHERE symbol=? AND market=? AND person_id=?",
                               symbol, market, session["user_id"])
            if len(stock) != 1:
                return apology("stock & market combination not matched")

            volume = int(request.form.get("shares"))
            if type(volume) != int or volume < 0:
                return apology("invalid number of shares")

            stock_id = stock[0]["stock_id"]
            # check if the symbol is in the portfolio
            if len(db.execute("SELECT * FROM portfolios WHERE stock_id=? AND person_id=?", stock_id, session["user_id"])) == 0:
                return apology("no such stock in your portfolio")

            # check if portfolio has enough stock
            inventory = db.execute("SELECT * FROM portfolios WHERE stock_id=? AND person_id=?",
                                   stock_id, session["user_id"])[0]["no_shs"]
            if volume > inventory:
                return apology("not enough shares in portfolio")
            else:
                cash_key = {'US':'cash_usd', 'GR':'cash_eur', 'VN':'cash_vnd'}[market]
                price = get_price_name(symbol, market)["price"]
                remaining = inventory - volume
                total = price * remaining
                cash_pre = db.execute("SELECT * FROM users WHERE id=?", session["user_id"])[0][cash_key]
                cash_balance = cash_pre + price * volume

                # update cash balance to users table
                command = f"UPDATE users SET {cash_key}=? WHERE id=?"
                db.execute(command, cash_balance, session["user_id"])

                # update share balance to table
                if remaining != 0:
                    db.execute("UPDATE portfolios SET no_shs=? WHERE stock_id=? AND person_id=?",
                               remaining, stock_id, session["user_id"])
                    db.execute("UPDATE portfolios SET total=? WHERE stock_id=? AND person_id=?",
                               total, stock_id, session["user_id"])
                else:
                    db.execute("DELETE FROM portfolios WHERE stock_id=? AND person_id=?", stock_id, session["user_id"])

                time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                db.execute("INSERT INTO transactions (person_id, stock_id, transaction_price, volume, time) VALUES (?, ?, ?, ?, ?)",
                           session["user_id"], stock_id, price, -volume, time)
                return redirect("/")


@app.route("/about-me", methods=["GET", "POST"])
#@login_required
def aboutme():
    if request.method == "GET":
        return render_template("aboutme.html")


@app.route("/aboutme", methods=["GET", "POST"])
def aboutme1():
    name = "Annonymous"
    email = "None"
    subject = "None"
    message = "New access see About me page"
    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    mess = db.execute("INSERT INTO messages VALUES (?, ?, ?, ?, ?)", time, 2, email, message, name)
    return redirect("/about-me")


@app.route("/contact", methods=["GET", "POST"])
@login_required
def contact():
    if request.method == "GET":
        message = []
        return render_template("contact.html", special_message=special_message)
    elif request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        subject = request.form.get("subject")
        message = request.form.get("message")
        time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        mess = db.execute("INSERT INTO messages VALUES (?, ?, ?, ?, ?)", time, session["user_id"], email, message, name)
        print(mess)
        message = ["Your message has been recorded. Thank you very much for your interest!","","","","",""]
        return render_template("contact.html", special_message=message)


@app.route("/evaluation", methods=["GET", "POST"])
@login_required
def evaluation():
    data = []
    markets = ["VN", "US", "GR"]
    portData = map_priceSeries_transactions(session["user_id"])
    for i in range(3):
        port = portData[i]
        startDate = port.index[0]
        market = markets[i]
        indexData = get_indexData(startDate, market)       
        df_merged = pd.merge(port, indexData, on="time")
        array = [df_merged.columns.tolist()] + df_merged.reset_index().values.tolist()
        array.remove(array[0])
        data.append(array)
    return render_template("evaluation.html", data_vn=data[0], data_us=data[1], data_gr=data[2])


@app.route("/message", methods=["GET", "POST"])
@login_required
def message():
	"""Read messages sent by users"""

	
@app.route("/test")
#@login_required
def test():
    #return render_template("reflux.html")
    yf_data = yfinance_json("^GSPC", "US", "", "", "1y")
    array = []
    for DP in yf_data:
        array.append([DP["dateTime"], DP["close"]])
    #data = db.execute("SELECT * FROM users")
    #return render_template("test2.html", array=array)
    return jsonify(yf_data)


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

if __name__ == '__main__':
    server_port = os.environ.get('PORT', '8080')
    app.run(debug=False, port=server_port, host='0.0.0.0')