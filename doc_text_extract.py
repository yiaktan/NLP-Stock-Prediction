import pandas as pd
import numpy as np
from config import Config
from SEC_Extractor import SEC_Extractor
from FinDataExtractor import FinDataExtractor
from tqdm import tqdm
import os
import math

quandl_key = Config.quandl_api_key
av_key = Config.av_api_key
sec_ext = SEC_Extractor
fin_data = FinDataExtractor(quandl_key,av_key)
no_parts = 2
part_no = 3

while part_no > no_parts:
    no_parts = int(input("Split data into how many parts?"))
    part_no = int(input("Which part is this?"))
    
chunksize = int(input("Number of rows to process at once (10 to 50 recommended)"))

#Load pickle
crawled_df = np.array_split(pd.read_pickle("Pickles/doc_links_df.pkl"),no_parts)[part_no-1]
crawled_len = len(crawled_df['txt_link'])
chunks = math.ceil(crawled_len/chunksize)
#Get link list length

for df in tqdm(np.array_split(crawled_df,chunks)):
    df['text'], df['release_date'] = zip(*df['txt_link'].apply(sec_ext.extract_text))
    df['items'] = df['text'].map(sec_ext.extract_item_no)
    #df[['price_change','vix']] = df[['ticker','release_date']].apply(fin_data.get_change,axis=1,broadcast=True)
    #df['rm_week'] = df[['ticker','release_date']].apply(fin_data.get_historical_movements,period="week",axis=1)
    #df['rm_month'] = df[['ticker','release_date']].apply(fin_data.get_historical_movements,period="month",axis=1)
    #df['rm_qtr'] = df[['ticker','release_date']].apply(fin_data.get_historical_movements,period="quarter",axis=1)
    #df['rm_year'] = df[['ticker','release_date']].apply(fin_data.get_historical_movements,period="year",axis=1)
    if not os.path.isfile('texts.csv'): #If no file exists, create one with header
        df.to_csv("Data/texts{}.csv.gzip".format(part_no),chunksize=chunksize,compression="gzip")
    else: # else it exists so append without writing the header
        df.to_csv("Data/texts{}.csv.gzip".format(part_no),mode="a",header=False,compression="gzip",chunksize=chunksize)       
