import datetime
import requests
import pandas as pd
import numpy as np
import quandl
from config import Config
import dateutil.relativedelta
import pandas_market_calendars as mcal
import io

# Returns Dataframe of document links for a given CIK
class FinDataExtractor:
    def __init__(self,quandl_key,av_key):
        # S&P 500 index data downloaded from Yahoo Finance GSPC
        self.gspc_df = pd.read_csv("Data/Indexes/gspc.csv",parse_dates=['Date'],index_col="Date")
        # Get VIX index data downloaded from Yahoo Finance
        self.vix_df = pd.read_csv("Data/Indexes/vix.csv",parse_dates=['Date'],index_col="Date")
        #Authenticate with API KEY
        quandl.ApiConfig.api_key = quandl_key
        self.av_key = av_key
        nyse = mcal.get_calendar('NYSE')
        self.nyse_holidays = nyse.holidays().holidays
    
#Takes datetime object and ticker string, returns price (opening or closing)
    def get_historical_movements(self,row,period):
        ticker,release_date = row[0],row[1]

       #1 Week
        if period == "week":
            e_start = release_date + datetime.timedelta(weeks=-1)
            b_start = e_start

            e_end = release_date + dateutil.relativedelta.relativedelta(days=-1)
            b_end = e_end

         #1 Month    
        elif period == "month":
            e_start = release_date + dateutil.relativedelta.relativedelta(months=-1)
            b_start = e_start + dateutil.relativedelta.relativedelta(days=-5)

            e_end = release_date + dateutil.relativedelta.relativedelta(days=-1)
            b_end = release_date + dateutil.relativedelta.relativedelta(days=-6)

        #1 Quarter
        elif period == "quarter":
            e_start = release_date + dateutil.relativedelta.relativedelta(months=-3)
            b_start = e_start + dateutil.relativedelta.relativedelta(days=-10)

            e_end = release_date + dateutil.relativedelta.relativedelta(days=-1)
            b_end = release_date + dateutil.relativedelta.relativedelta(days=-11)

        #1 Year
        elif period == "year":
            e_start = release_date + dateutil.relativedelta.relativedelta(years=-1)
            b_start = e_start + dateutil.relativedelta.relativedelta(days=-20)

            e_end = release_date + dateutil.relativedelta.relativedelta(days=-1)
            b_end = release_date + dateutil.relativedelta.relativedelta(days=-21)
        else:
            raise KeyError

        e_start = self.weekday_check(e_start)
        b_start = self.weekday_check(b_start)
        e_end = self.weekday_check(e_end)
        b_end = self.weekday_check(b_end)

        start_price = self.get_quandl_data(ticker=ticker,start_date = b_start, end_date = e_start)
        end_price = self.get_quandl_data(ticker=ticker,start_date = b_end, end_date = e_end)
        stock_change = self.calculate_pct_change(end_price,start_price)

        start_index = self.get_index_price(start_date = b_start, end_date = e_start)
        end_index = self.get_index_price(start_date = e_start, end_date = e_end)
        index_change =  self.calculate_pct_change(end_index,start_index)

        normalized = stock_change - index_change
        return normalized

    def get_quandl_data(self,ticker,start_date,end_date,market_open=False):
        if market_open == True:
            quandl_param = "WIKI/" + ticker + ".8"  
        else:
            quandl_param = "WIKI/" + ticker + ".11" 

        end_date_str = datetime.datetime.strftime(end_date,"%Y-%m-%d") 
        start_date_str = datetime.datetime.strftime(start_date,"%Y-%m-%d")
        price = quandl.get(quandl_param,start_date=start_date_str,end_date=end_date_str).mean()[0]

        if np.isnan(price).any():
            price = self.get_av_data(ticker,start_date,end_date,market_open)

        return price

    def get_av_data(self,ticker,start_date,end_date,market_open=False):
        start_date = start_date.date()
        end_date = end_date.date()

        url = "https://www.alphavantage.co/query?"
        params = {"function":"TIME_SERIES_DAILY_ADJUSTED",
                  "symbol":ticker,
                  "datatype":"csv",
                  "outputsize":"compact",
                  "apikey": self.av_key}
        r = requests.get(url,params)
        filepath = io.StringIO(r.content.decode('utf-8'))
        av_df = pd.read_csv(filepath,parse_dates=True,index_col=[0],error_bad_lines=False)
        try:
            if market_open == False:
                price = av_df.loc[end_date:start_date,"adjusted_close"].mean()
            else:
                price = av_df.loc[end_date:start_date,"open"].mean()
        except (KeyError,IndexError):
            price = np.nan
        return price


    # Takes ticker, 8K release date, checks time of release and then calculate before and after price change
    def get_change(self,row):
        release_date = row[1]
        ticker = row[0]
        market_close = release_date.replace(hour=16,minute=0,second=0)
        market_open = release_date.replace(hour=9,minute=30,second=0)

    # If report is released after market hours, take change of start date close and release date open
        if release_date > market_close:
            start_date = release_date
            end_date = release_date + datetime.timedelta(days=1)
            end_date = self.weekday_check(end_date)

            price_before_release = self.get_quandl_data(ticker,start_date,start_date,market_open=False)
            price_after_release = self.get_quandl_data(ticker,end_date,end_date,market_open=True)

            index_before_release = self.get_index_price(start_date,start_date,market_open=False)
            index_after_release = self.get_index_price(end_date,end_date,market_open=True)

            try:
                vix = self.vix_df.loc[self.vix_df.index == np.datetime64(start_date.date()),"Adj Close"][0].item()
            except IndexError:
                vix = np.nan

        # If report is released before market hours, take change of start date's close and release date's open
        elif release_date < market_open:
            start_date = release_date + datetime.timedelta(days=-1)
            start_date = self.weekday_check(start_date)
            end_date = release_date

            price_before_release = self.get_quandl_data(ticker,start_date,start_date,market_open=False)
            price_after_release = self.get_quandl_data(ticker,end_date,end_date,market_open=True) 

            index_before_release = self.get_index_price(start_date,start_date,market_open=False)
            index_after_release = self.get_index_price(end_date,end_date,market_open=True)
            try:
                vix = self.vix_df.loc[self.vix_df.index == np.datetime64(start_date.date()),"Adj Close"][0].item()
            except IndexError:
                vix = np.nan
        # If report is released during market hours, use market close
        else:
            start_date = release_date
            end_date = release_date
            price_before_release = self.get_quandl_data(ticker,start_date,start_date,market_open=True)
            price_after_release = self.get_quandl_data(ticker,end_date,end_date,market_open=False)

            index_before_release = self.get_index_price(start_date,start_date,market_open=True)
            index_after_release = self.get_index_price(end_date,end_date,market_open=False)
            
            try:
                vix = self.vix_df.loc[self.vix_df.index == np.datetime64(start_date.date()),"Open"][0].item()
            except IndexError:
                vix = np.nan
                
        price_pct_change = self.calculate_pct_change(price_after_release,price_before_release)
        index_pct_change = self.calculate_pct_change(index_after_release,index_before_release)
        normalized_change = price_pct_change - index_pct_change

        return normalized_change, vix

    def get_index_price(self,start_date,end_date,market_open=False):
        try:
            if market_open == True:
                price = self.gspc_df.loc[(self.gspc_df.index >= np.datetime64(start_date.date())) & 
                                 (self.gspc_df.index <= np.datetime64(end_date)),"Open"].mean()
            else:
                price = self.gspc_df.loc[(self.gspc_df.index >= np.datetime64(start_date.date())) & 
                                 (self.gspc_df.index <= np.datetime64(end_date)),"Adj Close"].mean()
        except IndexError:
                price = np.nan
        return price

    def calculate_pct_change(self,end_value,start_value):
        pct_change = (end_value - start_value) / start_value
        pct_change = round(pct_change,4) * 100
        return pct_change

    def weekday_check(self,date):  
        while date.isoweekday() > 5 or date.date() in self.nyse_holidays:
            date = date + datetime.timedelta(days=-1)
        return date