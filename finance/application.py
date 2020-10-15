import os

from cs50 import SQL
from datetime import datetime
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

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
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")

#4
@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    # Store the username of the user logged
    #userId = db.execute("SELECT id FROM users WHERE id = :idUser", idUser=int(session['user_id']))[0]["username"]


    #Selecting all portfolio of the current user logged in
    items = db.execute("SELECT symbol, shares FROM portfolio WHERE idUser = :idUser", idUser=session["user_id"])

    #innitialing the grand total
    gTotal = 0

    #Update the prince and total amount
    for item in items:
        #getting the data from databse
        symbol = item["symbol"]
        shares = item["shares"]
        stock = lookup(symbol)

        #calculating
        total_price = shares + stock["price"]
        gTotal += total_price
        db.execute("UPDATE portfolio SET price=:price, total=:total WHERE portfolio=:portfolio AND symbol=:symbol", price=usd(stock["price"]), total=usd(total_price), portfolio=session["user_id"], symbol=symbol)

    #Select the cash for each user
    cash = db.execute("SELECT cash from users WHERE id = :id", id=int(session["user_id"]))

    #Formatting cash and shares
    gTotal += cash[0]["cash"]

    #Getting the Table of portfolio
    table = db.execute("SELECT * from portfolio WHERE idUser = :idUser", idUser=int(session["user_id"]))
    #Showing the table on Home page (index)
    return render_template("index.html", stocks=table, cash = usd(cash[0]["cash"]), gTotal = usd(gTotal))

    # return apology("TODO")

#3
@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    #If submitted
    if request.method == "POST":
        #get stock invalid
        stock = lookup(request.form.get("symbol"))

        #if not stock
        if not stock:
            return apology("Sorry, invalid stock", 400)

        #check the shares
        try:
            #cating the shared number
            shares = int(request.form.get("shares"))
            if not shares.isdigit() or int(shares) < 1:
                return apology("Only > 1 number allowed", 400)
        except:
            return apology("Only  > 1 number allowed", 400)

        # Update history
        currentDate = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        db.execute("INSERT INTO history (symbol, shares, price, idUser, dateReg) VALUES(:symbol, :shares, :price, :idUser, :dateReg)",symbol=stock["symbol"], shares=shares, price=stock["price"], idUser=int(session["user_id"]), dateReg=currentDate)

        # Update the User's cash
        db.execute("UPDATE users SET cash = cash - :cash WHERE id = :id", cash=stock["price"] * shares, id=int(session["user_id"]))

        # Select user shares of specified symbol
        user_shares = db.execute("SELECT shares FROM portfolio WHERE idUser = :idUser AND symbol = :symbol", idUser=int(session["user_id"]), symbol=stock["symbol"])

        # If user has no shares of symbol, create new stock
        if not user_shares:
            user_shares = db.execute("INSERT INTO portfolio (name, symbol, shares, price, total, idUser) VALUES(:name, :symbol, :shares, :price, :total, :idUser)", name=stock["name"], symbol=stock["symbol"], shares=shares, price=stock["price"], total=usd(stock["price"] * shares), idUser=session["user_id"])

        # If user does have shares, increment the shares total
        else:
            sharesTotal = user_shares[0]["shares"] + shares
            db.execute("UPDATE portfolio SET shares = :shares WHERE symbol = :symbol AND idUser = :idUser", shares=sharesTotal, symbol=stock["symbol"], idUser=int(session["user_id"]))

        # Redirect user to index page after successfully transaction
        return redirect("/")

    else:
        return render_template("buy.html")

#6
@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    history = db.execute("SELECT * from history WHERE idUser = :idUser", idUser=int(session["user_id"]))

    return render_template("history.html", history=history)


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
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Flash info for the user
        #flash(f"Logged in as {request.form.get("username"))}")

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

#2
@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

    #If submmited
    if request.method == "POST":
        search = lookup(request.form.get("symbol"))

        #if symbol is invalid
        if not search:
            return apology("Invalid symbol. Please try again with another one.", 400)

        search["price"] = usd(search["price"])
        return render_template("quote_show.html", stock=search)

    else:
        return render_template("quote_show.html", stock=search)



#1
@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    #If submitting
    if request.method == "POST":

        #VALIDATIONS

        #Validating username filling
        if not request.form.get("username"):
            return apology("Please, insert the Username", 400)

        #Validating password filling
        if not request.form.get("password"):
            return apology("Please, insert the Password", 400)
        if not request.form.get("confirmation"):
            return apology("Please, insert the ConfirmationPassword", 400)

        #Validating passwords match
        elif request.form.get("password") != request.form.get("confirmation"):
                return apology("Sorry, the passwords does not match", 400)

        #Inserting the user
        query = db.execute("INSERT INTO users (username, hash) VALUES(:username, :hash)", username=request.form.get("username"), hash=generate_password_hash(request.form.get("password")))
        #if query didnt go properly
        if not query:
            return apology("Sorry, something went wrong", 400)

        #get the user Id
        session["user_id"] = query

        # Redirect user to login form
        return redirect("/")

    #if just opennig
    else:
        return render_template("register.html")

#5
@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    symbols = db.execute("SELECT symbol FROM portfolio WHERE idUser = :idUser", idUser=int(session["user_id"]))
    if request.method == "POST":

        if not request.form.get("symbol"):
            return apology("Please, select a symbol", 400)

        stock = lookup(request.form.get("symbol"))

        # Check symbol
        if not stock:
            return apology("invalid symbol", 400)

        # Check number of shares
        try:
            #casting the number
            sharesQtd = int(request.form.get("shares"))
            if not shares.isdigit() or int(shares) < 1:
                return apology("Only  > 1 number allowed", 400)
        except:
            return apology("Only  > 1 number allowed", 400)

        # Select the shares of the user
        user_shares = db.execute("SELECT shares FROM portfolio WHERE idUser = :idUser AND symbol = :symbol", idUser=int(session["user_id"]), symbol=stock["symbol"])

        # Check the stock of portfolio
        if not sharesQtd or user_shares[0]["shares"] < sharesQtd:
            return apology("Sorry, stock unavailable", 400)

        # Update history
        currentDate = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        db.execute("INSERT INTO history (symbol, shares, price, idUser, dateReg) VALUES(:symbol, :sharesQtd, :price, :idUser, :dateReg)", symbol=stock["symbol"], sharesQtd=-sharesQtd, price=stock["price"], idUser=session["user_id"], dateReg=currentDate)

        # Update the cash of the user
        db.execute("UPDATE users SET cash = cash + :cash WHERE id = :id", cash=stock["price"] * sharesQtd, id=int(session["user_id"]))

        # Select share for each (one) symbol
        user_shares = db.execute("SELECT shares FROM portfolio WHERE idUser = :idUser AND symbol = :symbol", idUser=int(session["user_id"]), symbol=stock["symbol"])

        # Reduce the shares quantity on user's total
        shares_count = user_shares[0]["shares"] - sharesQtd

        # Delete the item if user has no shares left
        if shares_count == 0:
            user_shares = db.execute("DELETE FROM portfolio WHERE idUser=:idUser AND name=:name", name=stock["name"], idUser=int(session["user_id"]))

        # Update the shared quantity, if user has stock
        else:
            db.execute("UPDATE portfolio SET shares = :shares WHERE symbol = :symbol AND idUser = :idUser", sharesQtd=shares_count, symbol=stock["symbol"], idUser=int(session["user_id"]))

        # Redirect user to index page after successfuly
        return redirect("/")
    else:
        return render_template("sell.html", symbols=symbols)


@app.route("/cash", methods=["GET", "POST"])
@login_required
def cash():
    """Add cash for the user"""
    if request.method == "POST":

        # Ensure user has specified cash to be added
        if not request.form.get("cash"):
            return apology("No cash was selected", 400)

        cash_to_add = request.form.get("cash")

        # Update user's cash
        db.execute("UPDATE users SET cash = cash + :added WHERE id = :id", added=cash_to_add, id=int(session["user_id"]))

        # Redirect user to index page after they make a purchase
        return redirect("/")

    else:
        return render_template("cash.html")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
