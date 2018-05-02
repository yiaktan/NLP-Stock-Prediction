from bs4 import BeautifulSoup
import datetime
import unicodedata
import requests
import pandas as pd
import numpy as np
from time import sleep
import re

class SEC_Extractor:
    def get_doc_links(cik,ticker):
        try:
            base_url = "https://www.sec.gov/cgi-bin/browse-edgar"
            inputted_cik = cik
            payload = {
                "action" : "getcompany",
                "CIK" : inputted_cik,
                "type" : "8-K",
                "output":"xml",
                "dateb" : "20180401",
            }
            sec_response = requests.get(url=base_url,params=payload)
            soup = BeautifulSoup(sec_response.text,'lxml')
            url_list = soup.findAll('filinghref')
            html_list = []
            # Get html version of links
            for link in url_list:
                link = link.string
                if link.split(".")[len(link.split("."))-1] == 'htm':
                    txtlink = link + "l"
                    html_list.append(txtlink)

            doc_list = []
            doc_name_list = []
            # Get links for txt versions of files
            for k in range(len(html_list)):
                txt_doc = html_list[k].replace("-index.html",".txt")
                doc_name = txt_doc.split("/")[-1]
                doc_list.append(txt_doc)
                doc_name_list.append(doc_name)
                # Create dataframe of CIK, doc name, and txt link
            df = pd.DataFrame(
                {
                "cik" : [cik]*len(html_list),
                "ticker" : [ticker]*len(html_list),
                "txt_link" : doc_list,
                "doc_name": doc_name_list
                }
            )
        except requests.exceptions.ConnectionError:
                sleep(.1)
        return df

    # Extracts text and submission datetime from document link
    def extract_text(link):
        try:
            r = requests.get(link)
            #Parse 8-K document
            filing = BeautifulSoup(r.content,"html5lib",from_encoding="ascii")
            #Extract datetime
            try:
                submission_dt = filing.find("acceptance-datetime").string[:14]
            except AttributeError:
                    # Flag docs with missing data as May 1 2018 10AM
                submission_dt = "20180501100000"
            
            submission_dt = datetime.datetime.strptime(submission_dt,"%Y%m%d%H%M%S")
            #Extract HTML sections
            for section in filing.findAll("html"):
                #Remove tables
                for table in section("table"):
                    table.decompose()
                #Convert to unicode
                section = unicodedata.normalize("NFKD",section.text)
                section = section.replace("\t"," ").replace("\n"," ").replace("/s"," ").replace("\'","'")
            filing = "".join((section))
        except requests.exceptions.ConnectionError:
                sleep(10)
        sleep(.1)

        return filing, submission_dt

    def extract_item_no(document):
        pattern = re.compile("Item+ +\d+[\:,\.]+\d+\d")
        item_list = re.findall(pattern,document)
        return item_list
