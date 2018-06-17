# Capstone Project 2 - NLP on SEC Reporting to Predict Stock Market Volatility

## 1. The Problem
In the financial services and banking industry, vast amounts of resources are dedicated to pouring over, analyzing, and attempting to quantify qualitative data from news and company reports. This problem is also constantly compounded as the news cycle shortens and reporting requirements for public companies become more onerous. In this project I attempt to demonstrate the viability of using natural language processing word embeddings on SEC 8-K documents with deep learning methods to predict stock price volatility after a company experiences a major event.

## 2. The Client
This project could be useful to hedge funds, banks, corporate finance offices, and anyone else involved in trading securities on public markets.

## 3. Methods
1. Data Collection & Preprocessing<br>
SEC 8K documents were scraped from the SEC's EDGAR database, with metadata such as date of document release and category of announcement (New agreements or acquisitions, revised financial expectations, etc.). Daily open and close prices for those companies were also collected via the AlphaVantage API, as well as the VIX and GSPSC indices from Yahoo Finance.<br>
Historical one year, one quarter, one month, and one week movements from the document release date were calculated using moving averages, normalized by changes in the S&P 500. 20,000 documents were scraped for all companies on the S&P 500. The target variable, "signal" was extracted by looking at the change in stock prices before and after a document was released (i.e. For a document released at 8pm Thursday, change in stock price from close on the release date to open price the next day, normalized by index change). A change greater than 1% was classified as up, less than -1% was classified as down, and anything in between as "stay". Document texts were preprocessed by removing non-alpha characters, stopwords, and punctuation, and lemmatization.
<br>
The size of the data was too large to handle on my 2012 MacBook Air, so I setup a high-memory Google Cloud Ubuntu instance to handle all data manipulations

2. Data Exploration<br>
Data was explored for distributions of document lengths, and category and class imbalances. A little less than half of all samples had signals of "up", which intuitively makes sense considering how stock prices rise over time, especially in the past five years. This means steps such as over or undersampling will have to take place before machine learning.

3. Machine Learning<br>
The GloVe 100 dimension word embeddings trained by Stanford NLP on Wikipedia was chosen as a compromise between having embeddings for esoteric, domain-specific vocabulary, and minimizing dimensionality in the dataset.<br>
I built 4 neural net architectures in Keras with Tensorflow backend in order to explore different methods of deep learning NLP (MLP, CNN, RNN (using GRU),CNN, and CNN+RNN).


## 4. Other Potential Datasets
There are many other ways this dataset could be augmented, such as by including other SEC reports such as 10Qs and 10Ks, texts from financial newspapers such as the Wall Street Journal, or financial data such as actual vs expected earnings per share.

## 5. Initial Findings
About half of all extracted trade signals were "up", meaning that the dataset has a class imbalance problem. This will need to be corrected using penalty or over/undersampling techniques. 
