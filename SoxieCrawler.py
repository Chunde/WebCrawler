import json
from json import dumps
import os
import time
#import urllib.request
from os.path import join
#import xlwt
#import shutil
import requests
from lxml import html
from multiprocessing import Process,Queue,Array,RLock,Lock
import multiprocessing
import threading
from Macro import _use_local_dealer_list_,_use_local_product_summary, _debug_,_wait_time_
from Utility import ParallelAgent
from PageAnalyser import *
current_path = os.path.dirname(os.path.abspath(__file__))
target_path = join(current_path,"Tables")
image_path = join("../../../","images")
lock = Lock()
all_dealer_list = []
all_product_list = []
page_content = None
def crawl_dealer_list_worker(ids):
    url_template = "https://sooxie.com/List.aspx?s={}&sc=null&Page={}"
    for id in ids:
        write_file_dir =join(target_path,"Dealers","Data")
        os.makedirs(write_file_dir, exist_ok=True)
        write_file_name = join(write_file_dir,id + ".json")

        if os.path.exists(write_file_name):
            print(write_file_name + " already downloaded, skip...")
            continue

        output = []
        check_unique = set()
        for i in range(5):
            url = url_template.format(id,i + 1)
            headers = { 
                "Accept":"*/*",
                "Accept-Encoding":"gzip, deflate, br",
                "Accept-Language":"zh-CN,zh;q=0.9",
                "Cache-Control":"max-age=0",
                "Cookie":"UM_distinctid=15e9dc2c3268d4-01fd1118393b7-e313761-1fa400-15e9dc2c327971; browse=268672; yunsuo_session_verify=4d70a592ac7f62ff57686e865df06973; __jsluid=63df15f5a355d2c5552f3f6efa77d551; CNZZDATA1253392690=999964383-1513727293-https%253A%252F%252Fsooxie.com%252F%7C1513727293; Hm_lvt_d7682ab43891c68a00de46e9ce5b76aa=1513732775; Hm_lpvt_d7682ab43891c68a00de46e9ce5b76aa=1513732775; Hm_lvt_d7682ab43891c68a00de46e9ce5b76aa=1513732775; Hm_lpvt_d7682ab43891c68a00de46e9ce5b76aa=1513733455",
                "Host":"sooxie.com",
                "Connection":"keep-alive",
                "Upgrade-Insecure-Requests":"1",
                "Referer":url,
                "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36"
                }

            page = requests.get(url, headers=headers)
            if not page:
                print("No data return from the server[{}]".format(id))
                return None
            tree = html.fromstring(page.content.decode('utf-8'))
            dealer_content = tree.xpath('//div[contains(@class, "message")]')
            if not dealer_content:
                break
            for item in dealer_content:
                dic = {}
                dic["Name"] = item.xpath('.//p[contains(@class,"storename")]/text()')[0]
                if dic["Name"] in check_unique:
                    continue
                orange_properties = item.xpath('.//p[contains(@class,"orange appr")]')#/html/body/div[3]/div[2]/div/div[11]/p[2]/em  /html/body/div[3]/div[2]/div/div[11]/p[3]/em
                if len(orange_properties) > 0:
                    dic["Market"] = orange_properties[0].xpath('.//em/text()')[0]
                if len(orange_properties) > 1:
                    dic["Rating"] = orange_properties[1].xpath('.//em/text()')[0]
                dic["URL"] = item.xpath('.//div[contains(@class,"sto_01")]/a/span/text()')[0] #/html/body/div[3]/div[2]/div/div[11]/div/a/span
                dic["Address"] =  item.xpath('.//p[contains(@class,"detaddr")]/text()')[0]#/html/body/div[3]/div[2]/div/div[1]/p[8]//<p class="detaddr">
                detmsg_properties = item.xpath('.//p[contains(@class,"detmsg")]')
                texts = []
                for data in detmsg_properties:
                    text = data.xpath('.//text()')
                    texts.extend(text)
                for i in range(len(texts)):
                    if texts[i].find("联系电话") != -1:
                        dic["Phone"] = texts[i + 1].strip()
                        continue
                    if texts[i].find("入驻时间")!= -1:
                        dic["Months"] = texts[i + 1].strip()
                        continue
                    if texts[i].find("QQ")!= -1:
                        dic["QQ"] = texts[i + 2].strip()
                        continue
                    if texts[i].find("产品")!= -1:
                        dic["Products"] = texts[i + 1].strip()
                        continue
                    if texts[i].find("会员")!= -1:
                        dic["Members"] = texts[i + 1].strip()
                        continue
                    if texts[i].find("下架")!= -1:
                        dic["Offlines"] = texts[i + 1].strip()
                        continue
                dic["Initial"] = id
                dic["Origin"]  = ''.join(texts)
                output.append(dic)
                check_unique.add(dic["Name"])

        with lock:
            all_dealer_list.extend(output)
        with open(write_file_name,'w',encoding = 'utf-8') as wf:
            json.dump(output,wf, ensure_ascii=False)
            print(write_file_name + " saved")

def crawl_dealer_list():
    parameters = []
    parameters.append('9')

    for i in range(26):
        char = ord('A') + i
        parameters.append(chr(char))
    ParallelAgent(parameters,crawl_dealer_list_worker,1)
    return all_dealer_list

def first_field(data):
    if len(data) > 0:
        return data[0]
    return None

def extract_content(product_list_content, output,left = False):
    for product in product_list_content:
            dic = {}
            dic["ProductID"] = product.xpath('.//li[contains(@class,"pname")]/a/text()')[0].split('：')[1]
            if left:
                dic["Price"] = first_field(product.xpath('.//div[contains(@class,"left")]/font/strong/text()'))
            else:
                dic["Price"] = first_field(product.xpath('.//li[contains(@class,"price")]/div/font/strong/text()'))
            dic["SName"] = first_field(product.xpath('.//li[contains(@class,"sname")]/text()'))
            dic["ProductURL"] = first_field(product.xpath('.//li[contains(@class,"img")]/a/@href'))
            dic["ImageURL"] = first_field(product.xpath('.//li[contains(@class,"img")]/a/img/@src'))
            output.append(dic)

def crawl_product_list_worker(dealers):
    for dealer in dealers:
        write_file_dir =join(target_path,"ProductSummary","Data")
        os.makedirs(write_file_dir, exist_ok=True)
        write_file_name = join(write_file_dir,dealer["Name"] + ".json")

        if os.path.exists(write_file_name):
            print(write_file_name + " already downloaded, skip...")
            continue
        output = []
        url = dealer["URL"]
        request_header = { 
            "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Encoding":"gzip, deflate, br",
            "Accept-Language":"zh-CN,zh;q=0.9",
            "Cache-Control":"max-age=0",
            "Connection":"keep-alive",
            "Cookie":"UM_distinctid=15e9dc2c3268d4-01fd1118393b7-e313761-1fa400-15e9dc2c327971; Hm_lvt_d7682ab43891c68a00de46e9ce5b76aa=1513732775; Hm_lpvt_d7682ab43891c68a00de46e9ce5b76aa=1513732775; browse=268672,266303,235755,264188; __jsluid=f2242960671471009b10c32e651db400",
            "Host":url,
            "If-Modified-Since":"Wed, 20 Dec 2017 09:21:13 GMT",
            "Upgrade-Insecure-Requests":"1",
            "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36",
            }
        #request_header = dumps(request_header), headers =request_header
        page = requests.get(url)
        if not page:
            print("No data for dealer[{}, URL={}], wait for {} seconds".format(dealer["Name"], dealer["URL"],_wait_time_))
            time.sleep(_wait_time_)
            continue
        tree = html.fromstring(page.content.decode('utf-8'))
        product_list_content = tree.xpath('//ul[contains(@class, "pro")]')
        if not product_list_content:
            print("No product list found for dealer[{}], wait for {} seconds".format(dealer["Name"],_wait_time_))
            time.sleep(_wait_time_)

            continue
        extract_content(product_list_content,output)

        #more page to load dynamically
        #view-source:https://90gc.sooxie.com/page.aspx?url=90gc&page=3&sort=&min=&max=
        extra_url_template = 'https://{}.sooxie.com/page.aspx?url={}&page={}&sort=&min=&max='
        indtxOfSlash = url.find('//')
        partial_url = url[indtxOfSlash + 2:].split('.')[0]
        page_num = 2
        while True:
            extra_url = extra_url_template.format(partial_url,partial_url,page_num)
            page = requests.get(extra_url)
            if not page or page.text == '':
                break
            page_content = page.content.decode('utf-8')
            tree = html.fromstring(page.content.decode('utf-8'))
            product_list_content = tree.xpath('//ul[contains(@class, "pro")]')
            if not product_list_content:
                break
            extract_content(product_list_content,output,True)
            page_num += 1

        
        for item in output:
            item["Dealer"] = dealer["Name"]
        with lock:
            all_product_list.extend(output)
       
        with open(write_file_name,'w',encoding = 'utf-8') as wf:
            json.dump(output,wf, ensure_ascii=False)
            print(write_file_name + " saved")
            print("Wait for {} seconds".format(_wait_time_))
            time.sleep(_wait_time_)
            print("Continue...")
     
def crawl_product_list_parallel(index_list):
    ParallelAgent(index_list,crawl_product_list_worker)
    return all_product_list
def crawl_page_list_parallel():
    read_file_dir =join(target_path,"ProductSummary","Data")
    fileNames = os.listdir(read_file_dir)
    for i in range(len(fileNames)):
        fileNames[i]  = join(read_file_dir,fileNames[i])
    ParallelAgent(fileNames,AnalysisPageWorker,10)
def LoadLocalData(source_dir):
    fileNames = os.listdir(source_dir)
    data_list = []
    for file in fileNames:
        if os.path.isdir(join(source_dir,file)):  
            continue
        try:
            with open(join(source_dir,file),'r',encoding ='utf-8') as rf:
                data = json.load(rf)
                data_list.extend(data)
        except:
            print(join(source_dir,file))
            os.remove(join(source_dir,file))
            continue
            

    return data_list

def LoadLocalDealerList():
    read_file_dir =join(target_path,"Dealers","Data")
    return LoadLocalData(read_file_dir)
def LoadLocalProductList():
    read_file_dir =join(target_path,"ProductSummary","Data")
    return LoadLocalData(read_file_dir)
def DownloadImageWorker(items):
    for item in items:
        os.makedirs(image_path, exist_ok=True)
        write_file_name = join(image_path,item["ImageURL"].split("/")[-1])

        if os.path.exists(write_file_name):
            print(write_file_name + " already downloaded, skip...")
            continue
        output = []
        url = item["ImageURL"]
        request_header = { 
            "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Encoding":"gzip, deflate, br",
            "Accept-Language":"zh-CN,zh;q=0.9",
            "Cache-Control":"max-age=0",
            "Connection":"keep-alive",
            "Cookie":"UM_distinctid=15e9dc2c3268d4-01fd1118393b7-e313761-1fa400-15e9dc2c327971; Hm_lvt_d7682ab43891c68a00de46e9ce5b76aa=1513732775; Hm_lpvt_d7682ab43891c68a00de46e9ce5b76aa=1513732775; browse=268672,266303,235755,264188; __jsluid=f2242960671471009b10c32e651db400",
            "Host":url,
            "If-Modified-Since":"Wed, 20 Dec 2017 09:21:13 GMT",
            "Upgrade-Insecure-Requests":"1",
            "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36",
            }
        #request_header = dumps(request_header), headers =request_header
        image = requests.get(url)
        if not image:
            continue
        with open(write_file_name,'wb') as wf:
            wf.write(image.content)
            print(write_file_name)

def DownloadProductImages(products):
    ParallelAgent(products,DownloadImageWorker,20)

if __name__ == '__main__':
    os.makedirs(target_path, exist_ok=True)
    index_list = None
    if _use_local_dealer_list_:
        index_list = LoadLocalDealerList()
    else:
        index_list = crawl_dealer_list()
    if not index_list:
        print("error, try later")
        exit(0)
    product_list = None
    if _use_local_product_summary:
        product_list = LoadLocalProductList()
    else:
        product_list = crawl_product_list_parallel(index_list)
        #已经抓取完，要抓取网页的，哈哈
    #DownloadProductImages(product_list);
    crawl_page_list_parallel()

