import pandas as pd
import requests
import numpy as np
from config import Config
import pandas_market_calendars as mcal
import datetime
from tqdm import tqdm
import io
import dateutil.relativedelta
from time import sleep

#Import all S&P 500 stock tickers
wiki_url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
cik_df = pd.read_html(wiki_url,header=[0],index_col=0)[0]
tickers = cik_df.index.drop_duplicates().values

all_tickers = dict()
av_key = Config.av_api_key

base_url = "https://www.alphavantage.co/query?"
params = {"function":"TIME_SERIES_DAILY_ADJUSTED",
          "datatype":"csv",
          "outputsize":"full",
          "apikey": av_key}

for ticker in tqdm(tickers):
    params["symbol"] = ticker
    r = requests.get(base_url,params)
    filepath = io.StringIO(r.content.decode('utf-8'))
    av_df = pd.read_csv(filepath,parse_dates=True,index_col=[0],error_bad_lines=False)
    all_tickers[ticker] = av_df
    sleep(1)
    
all_tickers_data = pd.concat(all_tickers)
all_tickers_data.to_pickle("all_tickers_data.pkl")
all_tickers_data.to_csv("all_tickers_data.csv",chunksize=50)