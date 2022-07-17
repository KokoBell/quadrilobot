#Import dependencies
from numpy import nan
from pandas._libs.tslibs import NaT
import telebot as tb
from telebot import types
import yfinance as yf
from time import sleep
import matplotlib.pyplot as plt
from PIL import Image

#Define variables. In this case, the API key.
BOT_INTERVAL = 0.1
BOT_TIMEOUT = 3

#Generate new bot instance
bot = tb.TeleBot(process.env.BOT_TOKEN)
actions = ["/start","/help"]

#The start and help functions help the user understand the functionality of the bot
@bot.message_handler(commands=["help"])
def help(message):
    bot.send_message(message.chat.id, "You can use the following commands: ", reply_markup=help_markup())
    commands = {"/start":"This is where you input the stock ticker of your choice. From here you can perform various functions on the stock using buttons as shown below.","/help":"Gives a list of all the available functions of Quadrilobot"}

    for command in commands:
        bot.send_message(message.chat.id, str(command)+"\n"+str(commands[command]), reply_markup=help_markup())
        sleep(0.4)

    bot.send_message(message.chat.id,"You can use the following buttons on your stock:", reply_markup=help_markup())

    requests = {"All":"This returns all the data available on the particular stock on Yahoo Finance.",
        "Financials":"This returns the financial data of the stock.",
        "B-Sheet":"This returns the balance sheet data for the stock.",
        "Cashflow":"This returns the cashflow data of the given the stock.",
        "Earnings":"This returns the earnings data for the stock.",
        "Revenue":"This returns the yearly revenue for the last 4 years of a stock if available.",
        "Dividends":"This returns all the dividend data of a given stock.",
        "Price":"This returns an graph of the past month's close price for the stock.",
        "PB":"This returns the price to book ratio of your stock.",
        "PE":"This returns the price-to-earnings ratio of a given stock."}

    for i in requests:
        bot.send_message(message.chat.id,str(i)+"\n"+str(requests[i]), reply_markup=help_markup())
        sleep(0.4)

@bot.message_handler(commands=["start"])
def start(message):
    response = "Enter a stock ticker of your choice..."
    stock = bot.send_message(message.chat.id, response, reply_markup=start_markup())
    bot.register_next_step_handler(stock, start_research)

def start_research(message):
    ticker_symbol = message.text.upper()

    if ticker_symbol.lower() == "/help":
        help(message)
    else:
        ticker_data = yf.Ticker(ticker_symbol).info
        response = f"Select one of the options for data on {ticker_symbol}"
        keys = list(ticker_data)

    if ticker_data["regularMarketPrice"] != None and len(keys) != 2:
        bot.send_message(message.chat.id, response, reply_markup=markup(ticker_symbol))
    else:
        response = "Uh oh! It seems like that ticker was incorrect. Please check your spelling and try again."
        bot.send_message(message.chat.id, response)
        start(message)

def exit_request(message):
    request = message.text.split()
    if request[0].lower().startswith("exit"):
        return True
    else:
        return False   

@bot.message_handler(func=exit_request)
def exit_stock(message):
    start(message)

def markup(ticker_symbol):
    markup = types.ReplyKeyboardMarkup()
    markup.row(f'All {ticker_symbol}')
    markup.row(f'Financials {ticker_symbol}', f'B-Sheet {ticker_symbol}', f'Cashflow {ticker_symbol}')
    markup.row(f'Dividends {ticker_symbol}',f'Revenue {ticker_symbol}',f'Earnings {ticker_symbol}')
    markup.row(f'Price {ticker_symbol}',f'PB {ticker_symbol}',f'PE {ticker_symbol}', f'Sustainability {ticker_symbol}')
    markup.row(f"Exit")
    return markup

def start_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, input_field_placeholder="e.g. PPE.JO", one_time_keyboard=True)
    markup.add("/help")
    return markup

def help_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("/start","/help")
    return markup

#Helper functions for formatting monetary values
def formatter(currency,value):
    if currency == "USD":
        if value >= 0:
            return "$"+str(remove_zeros(value))
        else:
            return "-$"+str(remove_zeros(-1*value))
    elif currency == "ZAR":
        if value >= 0:
            return "R"+str(remove_zeros(value))
        else:
            return "-R"+str(remove_zeros(-1*value))
    else:
        return str(value)

def remove_zeros(value):
    reverse_value = str(value)
    reverse_value = reverse_value[0:len(reverse_value)-2]
    if len(reverse_value)<7:
        return str(value)
    elif len(reverse_value) >= 7 and len(reverse_value) < 10:
        reverse_value = float(round(value/1000000,2))
        return str(reverse_value)+" Million"
    elif len(reverse_value) >= 10 and len(reverse_value) < 13:
        reverse_value = float(round(value/1000000000,2))
        return str(reverse_value)+" Billion"
    elif len(reverse_value) >= 13:
        reverse_value = float(round(value/1000000000000,2))
        return str(reverse_value)+" Trillion"

#Custom function for the  handler to parse through the user request
def all_request(message):
    request = message.text.split()
    if len(request) < 2 or request[0].lower() not in "all":
        return False
    else:
        return True

#Requesting data using text
@bot.message_handler(func=all_request)
def send_all_data(message):
    ticker_symbol = message.text.split()[1].upper()
    ticker_data = yf.Ticker(ticker_symbol).info
    if ticker_data["regularMarketPrice"] != None and ticker_data["logo_url"] != "":
        response = f"All the data for {ticker_symbol}: \n"
        bot.send_message(message.chat.id, response)

        for i in ticker_data:
            if ticker_data[i]!=None and i!="logo_url" and i!="zip" and i!="maxAge" and i!="companyOfficers":
                response = str(i) +":  "+str(ticker_data[i])+"\n"
                bot.send_message(message.chat.id, response, disable_notification=False, reply_markup=markup(ticker_symbol))
                sleep(0.6)
    else:
        response = "Uh oh! It seems like that ticker was incorrect. Please check your spelling and try again."
        bot.send_message(message.chat.id,response)

    #Requesting dividend data using text
def dividend_request(message):
    request = message.text.split()
    if len(request) < 2 or not request[0].lower().startswith("dividend"):
        return False
    else:
        return True

@bot.message_handler(func=dividend_request)
def send_dividends(message):
    ticker_symbol = message.text.split()[1].upper()
    dividend_data = yf.Ticker(ticker_symbol).dividends.reset_index()
    limit = 10
    if len(dividend_data["Dividends"])>1:
        bot.send_message(message.chat.id,f"Dividend data for {ticker_symbol}: \n")
        response = "Date" + 11*" "+"Dividends"
        bot.send_message(message.chat.id,response)
        if len(dividend_data["Dividends"])<limit:
            for i in range(len(dividend_data["Dividends"])-1,0,-1):
                date_ = dividend_data["Date"][i]
                date_ = str(date_)
                date_ = date_[0:11]
                div = dividend_data["Dividends"][i]
                response = str(date_) + ": " + str(div)
                bot.send_message(message.chat.id, response, reply_markup=markup(ticker_symbol))
                sleep(0.4)
        else:
            for i in range(len(dividend_data["Dividends"])-1,len(dividend_data["Dividends"])-limit,-1):
                date_ = dividend_data["Date"][i]
                date_ = str(date_)
                date_ = date_[0:11]
                div = dividend_data["Dividends"][i]
                response = str(date_) + " : " + str(div)
                bot.send_message(message.chat.id,response)
                sleep(0.4)
    else:
        response = "No dividend data was found."
        bot.send_message(message.chat.id,response)

#Custom function to validate the earnings data of the stock
def validator(calender_data):
    try:
        index = "Value"
        values = calender_data[index]
    except:
        try:
            index = 0
            values = calender_data[index]
        except:
            return (False,None)

    count = 0
    for i in values:
        if str(i) == str(NaT):
            count += 1

    if count == len(values)-1:
        return (False,None)
    else:
        return (True,index)

#Custom function for the  handler to parse through the user request
def earnings_request(message):
    request = message.text.split()
    if len(request) < 2 or not request[0].lower().startswith("earning"):
        return False
    else:
        return True

#Requesting data using text
@bot.message_handler(func=earnings_request)
def send_earnings(message):    
    ticker_symbol = message.text.split()[1].upper()
    calender_data = yf.Ticker(ticker_symbol).calendar.reset_index()
    val,index = validator(calender_data)

    if bool(val) == True:
        response = f"Here is the earnings data for {ticker_symbol}: "
        bot.send_message(message.chat.id,response)
            
        for i in calender_data.index:
            if str(calender_data[index][i]) != "None":
                response = str(calender_data["index"][i])+" : "+str(calender_data[index][i])
                bot.send_message(message.chat.id,response)
                sleep(0.4)
    else:
        response = "No earnings data was found for this stock."
        bot.send_message(message.chat.id,response)

def pe_request(message):
    request = message.text.split()
    if len(request) < 2 or not request[0].lower().startswith("pe"):
        return False
    else:
        return True    

@bot.message_handler(func=pe_request)
def send_pe(message):
    ticker_symbol = message.text.split()[1].upper()
    ticker_data = yf.Ticker(ticker_symbol).info
    response = ""
    if ticker_data["regularMarketPrice"] != None and ticker_data["trailingEps"] != None:
        pe = ticker_data['trailingPE']
        response = f'The Price to Earnings Ratio of {ticker_symbol} is: %.2f' % pe
        bot.send_message(message.chat.id, response)
    else:
        response = "No PE data found for this stock."
        bot.send_message(message.chat.id, response)

def pb_request(message):
    request = message.text.split()
    if len(request) < 2 or not request[0].lower().startswith("pb"):
        return False
    else:
        return True    

@bot.message_handler(func=pb_request)
def send_pb(message):
    ticker_symbol = message.text.split()[1].upper()
    ticker_data = yf.Ticker(ticker_symbol).info
    response = ""
    if ticker_data["priceToBook"] != None:
        pb = ticker_data['priceToBook']
        response = f'The Price to Book Ratio of {ticker_symbol} is: %.2f' % pb
        bot.send_message(message.chat.id, response)
    else:
        response = "No price to book data found for this stock."
        bot.send_message(message.chat.id, response)

def price_request(message):
    request = message.text.split()
    if len(request) < 2 or not request[0].lower().startswith("price"):
        return False
    else:
        return True    

@bot.message_handler(func=price_request)
def send_price(message):
    ticker_symbol = message.text.split()[1].upper()
    ticker = yf.Ticker(ticker_symbol)
    ticker_data = ticker.info
    price_data = ticker.history()

    if ticker_data["regularMarketPrice"] != None and ticker_data["trailingEps"] != None:
        response = f"Here is a snapshot of the past month's closing prices for {ticker_symbol}"
        # Plot adjusted close price data
        plt.switch_backend("agg")

        price_data['Close'][::].plot(figsize=(10,7))

        plt.title("Close price of %s" % ticker_symbol, fontsize=16)

        # Define the labels for x-axis and y-axis
        plt.ylabel('Price', fontsize=14)
        plt.xlabel('Date', fontsize=14)

        # Plot the grid lines
        plt.grid(which="major", color='k', linestyle='-.', linewidth=0.5)

        # Send the plot
        filepath = "price_data.png"
        plt.savefig(filepath,bbox_inches="tight",pad_inches=1)
        im = Image.open(filepath,mode="r")
        bot.send_photo(message.chat.id,im)
    else:
        response = "No price data found for this stock."
        bot.send_message(message.chat.id, response)

def revenue_request(message):
    request = message.text.split()
    if len(request) < 2 or not request[0].lower().startswith("revenue"):
        return False
    else:
        return True    

@bot.message_handler(func=revenue_request)
def send_revenue(message):
    ticker_symbol = message.text.split()[1].upper()
    ticker = yf.Ticker(ticker_symbol)
    ticker_data = ticker.info
    if ticker_data["regularMarketPrice"] != None and ticker_data["logo_url"] != "":
        response = f"Here is the revenue information for {ticker_symbol}: "
        bot.send_message(message.chat.id,response)
        currency = ticker_data["financialCurrency"]
        revenue = ticker.financials.loc["Total Revenue"]
        response = "Date"+ 11*" "+"Revenue"
        bot.send_message(message.chat.id,response)
        for i in revenue.index:
            response = str(i)[0:11]+":  "+formatter(currency,revenue[i])
            bot.send_message(message.chat.id,response)
    else:
        response = "Uh oh! It seems like that ticker was incorrect. Please check your spelling and try again."
        bot.send_message(message.chat.id,response)

def financials_request(message):
    request = message.text.split()
    if len(request) < 2 or not request[0].lower().startswith("financ"):
        return False
    else:
        return True    

@bot.message_handler(func=financials_request)
def send_financials(message):
    ticker_symbol = message.text.split()[1].upper()
    ticker = yf.Ticker(ticker_symbol)
    ticker_data = ticker.info
    ticker_finance = ticker.financials

    if ticker_data["regularMarketPrice"] != None and ticker_data["logo_url"] != "":
        response = f"Here is the financial statement information for {ticker_symbol}: "
        bot.send_message(message.chat.id,response)
        currency = ticker_data["financialCurrency"]
        for i in ticker_finance.index:
            ind = ticker_finance.loc[i].index[0]
            price = ticker_finance.loc[i][ind]
        
            if price != None:
                response = str(i)+": "+formatter(currency,price)
                bot.send_message(message.chat.id,response)
    else:
        response = "Uh oh! It seems like that ticker was incorrect. Please check your spelling and try again."
        bot.send_message(message.chat.id,response)

def balance_request(message):
    request = message.text.split()
    if len(request) < 2 or not request[0].lower().startswith("b-sheet"):
        return False
    else:
        return True    

@bot.message_handler(func=balance_request)
def send_balance_sheet(message):
    ticker_symbol = message.text.split()[1].upper()
    ticker = yf.Ticker(ticker_symbol)
    ticker_data = ticker.info
    ticker_balance = ticker.balance_sheet

    if ticker_data["regularMarketPrice"] != None and ticker_data["logo_url"] != "":
        currency = ticker_data["financialCurrency"]
        response = f"Here is the balancesheet data for {ticker_symbol}: "
        bot.send_message(message.chat.id,response)
        for i in ticker_balance.index:
            ind = ticker_balance.loc[i].index[0]
            price = ticker_balance.loc[i][ind]
        
            if price != None and str(price).lower() != str(nan):
                response = str(i)+": "+formatter(currency,price)
                bot.send_message(message.chat.id,response)
    else:
        response = "Uh oh! It seems like that ticker was incorrect. Please check your spelling and try again."
        bot.send_message(message.chat.id,response)

def cashflow_request(message):
    request = message.text.split()
    if len(request) < 2 or not request[0].lower().startswith("cash"):
        return False
    else:
        return True    

@bot.message_handler(func=cashflow_request)
def send_cashflow(message):
    ticker_symbol = message.text.split()[1].upper()
    ticker = yf.Ticker(ticker_symbol)
    ticker_data = ticker.info
    ticker_cashflow = ticker.cashflow

    if ticker_data["regularMarketPrice"] != None and ticker_data["logo_url"] != "":
        response = f"Here is the cashflow information for {ticker_symbol}: "
        bot.send_message(message.chat.id,response)
        for i in ticker_cashflow.index:
            currency = ticker_data["financialCurrency"]
            ind = ticker_cashflow.loc[i].index[0]
            price = ticker_cashflow.loc[i][ind]
        
            if price != None and str(price).lower() != str(nan):
                response = str(i)+": "+formatter(currency,price)
                bot.send_message(message.chat.id,response)
    else:
        response = "Uh oh! It seems like that ticker was incorrect. Please check your spelling and try again."
        bot.send_message(message.chat.id,response)

def sustainability_request(message):
    request = message.text.split()
    if len(request) < 2 or not request[0].lower().startswith("sustain"):
        return False
    else:
        return True    

@bot.message_handler(func=sustainability_request)
def send_sustainability(message):
    ticker_symbol = message.text.split()[1].upper()
    ticker = yf.Ticker(ticker_symbol)
    ticker_data = ticker.info
    ticker_sustainability = ticker.sustainability

    if ticker_data["regularMarketPrice"] != None and ticker_data["logo_url"] != "":
        if str(type(ticker_sustainability)) != "<class 'NoneType'>":
            response = f"Here is the sustainability data for {ticker_symbol}: "
            bot.send_message(message.chat.id,response)
            for i in ticker_sustainability["Value"].index:
                price = ticker_sustainability["Value"][i]
        
                if str(price) != str(None) and str(price).lower() != str(nan):
                    response = str(i)+": "+str(price)
                    bot.send_message(message.chat.id,response)
        else:
            response = "Sustainability information is unavailable."
            bot.send_message(message.chat.id,response)

    else:
        response = "Uh oh! It seems like that ticker was incorrect. Please check your spelling and try again."
        bot.send_message(message.chat.id,response)

while True:
    try:
        bot.polling()
    except:
        sleep(1)