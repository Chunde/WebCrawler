import json
from json import dumps
import os
from selenium import webdriver
import time
from os.path import join
import requests
from lxml import html
from multiprocessing import Process,Queue,Array,RLock,Lock
import multiprocessing
import threading
from Macro import _use_local_dealer_list_,_use_local_product_summary, _debug_,_wait_time_
from Utility import ParallelAgent

current_path = os.path.dirname(os.path.abspath(__file__))
target_path = join(current_path,"Tables")

chromeOptions = webdriver.ChromeOptions()
prefs = {"profile.managed_default_content_settings.images":2}
chromeOptions.add_experimental_option("prefs",prefs)
chromeOptions.add_argument('--headless')
chromeOptions.add_argument("--log-level=3")

chromeOptions.add_argument('--disable-gpu')  # Last I checked this was necessary.
driver = webdriver.Chrome('C:\\Program Files (x86)\\Google\\Chrome\\Application\\chromedriver.exe',chrome_options=chromeOptions)  # Optional argument, if not specified will search path.

    

def AnalysisPage(file, items):
    #if "新时代鞋业" not in file:
    #    return;
    write_file_dir =join(target_path, "ShoesDescriptor","Data")
    os.makedirs(write_file_dir, exist_ok=True)
    write_file_name = join(write_file_dir, file.split("\\")[-1])
    print(write_file_name)
    if os.path.exists(write_file_name):
        print(write_file_name + " already downloaded, skip...")
        return
    output = []
    n = 0
    html_src_dir = join(target_path, "ShoesDescriptor", "html",file.split("\\")[-1].split(".")[0])
    os.makedirs(html_src_dir, exist_ok=True)
    for item in items:
        url = item["ProductURL"]
        html_file = join(html_src_dir, item["ProductID"].__str__() + ".html")
        n +=1
        print((item["Dealer"] + ":" + n.__str__()))
        retry = False
        while(True):
            html_source = None
            if os.path.exists(html_file):
                print(html_file + " exists, use local file")
                with open(html_file,'r',encoding = 'utf-8') as fr:
                    html_source = fr.read()
            else:
                time.sleep(1)
                driver.get(url)
                html_source = driver.page_source

            if not html_source:
                print("空页面，停止！")
                return
            tree = html.fromstring(html_source)
            dic = {}
            dic["ID"] = item["ProductID"]
            dic["Url"] = url
            dic["ThumbUrl"] = item["ImageURL"]
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
                    #if type(dic["Price"]) == type([]):
                    #    print("")

                elif key[0] == "人":
                    dic["Views"] = m.xpath('.//strong/text()')[0]
                    dic["UpdateDes"] = m.xpath('.//strong/font/text()')[0]
            details = tree.xpath('//div[contains(@class, "prodetails")]/div/ul/li/text()')
            for d in details:
                tks = d.split(":")
                if len(tks) != 2:
                    print(d)
                    continue
                key = tks[0].strip()
                if key == "发布时间":
                    dic["DebutTime"] = tks[1]
                    continue
                elif key == "鞋垫":
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
            dic["Dealer"] = file.split("\\")[-1].split(".")[0]
            output.append(dic)
           # print(dic)
            if not os.path.exists(html_file):
                with open(html_file,'w',encoding = 'utf-8') as f:
                    f.write(html_source)
            break

    with open(write_file_name,'w',encoding = 'utf-8') as wf:
            json.dump(output,wf, ensure_ascii=False)
            print(write_file_name + " saved")

def AnalysisPageWorker(fileNames):
    for file in fileNames:
        try:
            with open(file,'r',encoding ='utf-8') as rf:
                items = json.load(rf)
                AnalysisPage(file,items);
        except:
            continue
   

        