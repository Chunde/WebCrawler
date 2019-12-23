#!/usr/bin/env python3
import json
from json import dumps
import os
import time
from os.path import join
import datetime
import requests
from lxml import html
from multiprocessing import Process,Queue,Array,RLock,Lock
import multiprocessing
import threading
from Macro import _use_local_dealer_list_,_use_local_product_summary, _debug_,_wait_time_
from Utility import ParallelAgent
#from PageAnalyser import *
current_path = os.path.dirname(os.path.abspath(__file__))
target_path = join(current_path,"Tables")
image_path = join("../../../","images");
lock = Lock()
import importlib
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.inspection import inspect
from sqlalchemy.exc import OperationalError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


from data_model_base import (
    import_data_model,
    is_primary_key,
    get_tables_list,
)
all_dealer_list = []
all_product_list = []
page_content = None


def CrawlNewItem(url, session, data_model):
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
        print("No data return from the server[{}. Exit]".format(id))
        exit()
        return True
    tree = html.fromstring(page.content.decode('utf-8'))
    content = tree.xpath('//ul [contains(@class, "pro")]')
    if not content:
        return True
    for item in content:
        ThumbUrl = item.xpath('.//li[contains(@class,"img")]/a/img/@src')
        if len(ThumbUrl) == 0:
            continue
        ThumbUrl = ThumbUrl[0]
        Dealer =item.xpath('.//li[contains(@class,"pname")]/a/text()')[0]
        tks = Dealer.split('：')
        productID = tks[1].strip()
        Dealer = tks[0].split(' ')[0].strip()
        ProductUrl = item.xpath('.//li[contains(@class,"img")]/a/@href')[0]
        Title = item.xpath('.//li[contains(@class,"sname")]/text()')[0]
        if(len(ProductUrl) > 10 ):
            if extract_content(ProductUrl,Dealer,productID,ThumbUrl, session, data_model) == False:
                return False

    return True

def save_to_DB(data, session, data_model):
        session.add(data_model(**data))
        session.commit()


def extract_content(url,dealer, productID, ThumbUrl, session, data_model):
    html_src_dir = join(target_path,"ShoesDescriptor","html",dealer)
    os.makedirs(html_src_dir, exist_ok=True)
    html_file = join(html_src_dir, productID.replace('/','-').__str__() + ".html")
    retry = True #not necessary if time delayed for javascript
    localFlag = False
    while(True):
        html_source = None;
        if os.path.exists(html_file):
            #print(html_file + " 已经存在，直接跳过")
            return True
            with open(html_file,'r',encoding = 'utf-8') as fr:
                    html_source = fr.read()
                    localFlag = True
        else:
            page = requests.get(url)
            #driver.get(url);
            time.sleep(1);
            html_source = page.content.decode('utf-8') #driver.page_source;

        if not html_source:
            print("空页面，停止！")
            return True
        tree = html.fromstring(html_source)
        dic = {}
        dic["ID"] = productID
        dic["Url"] = url
        dic["ThumbUrl"] = ThumbUrl
        title = tree.xpath('//div[contains(@class, "infobox_h")]/h2/text()')[0]
        dic["Title"] = title.strip()
        metas = tree.xpath('//div[contains(@class, "infobox_h")]/div[contains(@class, "infoline bline")]')
        for m in metas:
            key = m.xpath('.//b/text()')[0]
            if key[0] == "尺":
                dic["Sizes"] = "|".join(m.xpath('.//ul/li/a/text()'))
            elif key[0] == "颜":
                dic["Colors"] = "|".join(m.xpath('.//ul/li/a/text()'))
            elif key[0] == "发":
                dic["Price"] = m.xpath('.//em/text()')[0]
            elif key[0] == "人":
                dic["Views"] = m.xpath('.//strong/text()')[0].strip()
                dic["Date"] = m.xpath('.//strong/font/text()')[0].strip()
                if not localFlag and dic["Date"]  != "今日新款，放心上传":
                    return False
                dic["Date"]  = datetime.datetime.now().strftime("%Y-%m-%d  %H:%M")
                dic["DebutTime"] = datetime.datetime.now().strftime("%Y-%m-%d")
        details = tree.xpath('//div[contains(@class, "prodetails")]/div/ul/li/text()')
        for d in details:
            tks = d.split(":")
            if len(tks) != 2:
                print(d)
                continue
            key = tks[0].strip()
          
            if key == "鞋垫":
                dic["Insoles"] = tks[1]
            elif key == "品牌":
                dic["Brand"] = tks[1]
            elif key == "鞋头款式":
                dic["HeadStyle"] = tks[1]
            elif key == "闭合方式":
                dic["CloseStyle"] = tks[1]
            elif key == "鞋底材质":
                dic["SoleMaterial"] = tks[1]
            elif key == "帮面材质":
                dic["FaceMaterial"] = tks[1]
            elif key == "鞋面内里材质":
                dic["InnerFaceMaterial"] = tks[1]
            elif key == "制作工艺":
                dic["AssembleMethod"] = tks[1]
            elif key == "跟底款式":
                dic["HeelStyle"] = tks[1]
            elif key == "鞋跟":
                dic["HeelHeight"] = tks[1]
            elif key == "样式":
                dic["Patterns"] = tks[1]
            elif key == "流行元素":
                dic["StylishElements"] = tks[1]
            elif key == "风格":
                dic["Style"] = tks[1]
            elif key == "场合":
                dic["Scene"] = tks[1]
            elif key == "季节":
                dic["Season"] = tks[1]
            elif key == "款式":
                dic["SheosType"] = tks[1]
            elif key == "功能":
                dic["Functionality"] = tks[1]
            elif key == "适用对象":
                dic["Subjects"] = tks[1]
            elif key == "图案":
                dic["Pattern"] = tks[1]

        if not retry and ("HeadStyle" not in dic):
            print("Retry:" + url)
            retry = True
            continue
        previewImgs = tree.xpath('//div[contains(@id, "jqlist")]/ul/li/img/@bimg')
        showImgs = tree.xpath('//div[contains(@class, "prodetails")]/p/img/@data-url')
        latestImgs = tree.xpath('//div[contains(@class, "newprolist")]/ul/li/p/img/@data-url')
        dic["GalleryURLs"] = "|".join(showImgs);
        dic["PreviewURLs"] = "|".join(previewImgs);
        dic["Dealer"] = dealer
#        print(dic)
        if not os.path.exists(html_file):
            try:
                with open(html_file,'w',encoding = 'utf-8') as f:
                    html_source = html_source.replace("今日新款，放心上传",datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
                    f.write(html_source)
                    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M\t") + html_file + " saved")
            except:
                pass
        save_to_DB(dic,session,data_model)
        return True

#a dictionary for check unique entry
unique_dic = {}

def process_each_data(raw_data, data_model):
    data = {}
    for key, value in raw_data.items():
        column = getattr(data_model, key)
        data[key] = column.preprocess(value)
        if is_primary_key(column, data_model) and data[key] == None:
            print("null primary key in: {}".format(raw_data))
            return None
    return data

def generte_dic_key(data_model, dic={}):

    keys = []
    for i in inspect(data_model).primary_key:
        keys.append(i.name)
    keys.sort()
    key = ""
    for item in keys:
        key = key + dic[item].__str__()
    return key

def import_to_db(engine, data_model):
    n = 0
    try:
        data_model.__table__.drop(engine);
    except OperationalError:
        pass
    data_model.base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    onlyfiles = [f for f in listdir(
        data_model.json_files_path
    ) if isfile(join(data_model.json_files_path, f))]
    # print(len(onlyfiles))
    for file_name in onlyfiles:
        abs_file_name = join(data_model.json_files_path, file_name)
        #if(file_name != "恒达顺.json"):
        #    continue

        print("Importing: " + abs_file_name)
        #try:
        with open(abs_file_name, 'r',encoding ='utf-8') as f:
            raw_data = json.load(f)
            if type(raw_data) == type({}):
                data = process_each_data(raw_data, data_model)
                if data == None:
                    continue
                session.add(data_model(**data))
            elif type(raw_data) == type([]):
                for raw_each_data in raw_data:
                    
                    each_data = process_each_data(raw_each_data, data_model)
                    if each_data == None:
                        continue

                    key = generte_dic_key(data_model,each_data)

                    if key in unique_dic: # if a entry already exists, skip
                        continue
                    unique_dic[key] = 1

                    session.add(data_model(**each_data))
        session.commit()
        n = n +1
        print( ":\t" + abs_file_name + " imported(" + n.__str__() + "/" + len(onlyfiles).__str__() + ")")
        #except:
        #    print("Import Failed " + abs_file_name)
        #    continue

if __name__ == '__main__':
    engine = create_engine('sqlite:///{}'.format(join(current_path,"../Database.db")),connect_args={'timeout': 3600})
    data_model = import_data_model('ShoesDescriptor')

    #try:
    #    data_model.__table__.drop(engine);
    #except OperationalError:
    #    pass
    while(True):
        try:
            data_model.base.metadata.create_all(engine)
            Session = sessionmaker(bind=engine)
            session = Session()

            while(True): # never stop updating
                page_num = 1
                url_template = "https://sooxie.com/?Page={}&sort=1"

                url = url_template.format(page_num)
                while(CrawlNewItem(url, session, data_model)):
                    page_num += 1
                    url = url_template.format(page_num)
                    time.sleep(1);
                print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M\t") + "一轮更新结束，2分钟后重新开始")  
                time.sleep(120)
        except:
            pass
        print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M\t") + "Exception occurs, resuming...")
        time.sleep(1);
      
