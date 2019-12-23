
import json
import os
import re
import sys
import inspect

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir)
sys.path.insert(0,parentdir+"/../")

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from data_model_base import Integer, String, Float, Percentage, Column, Date
from sqlalchemy.orm import sessionmaker
from os import listdir
from os.path import isfile, join

Base = declarative_base()
current_path = os.path.dirname(os.path.abspath(__file__))

class ShoesDescriptor(Base):
    base =  Base
    json_files_path = join(current_path, "data")
    __tablename__ = "ShoesDescriptor"
    UserName= Column(String(desc="用户名"))
    Dealer = Column(String(desc="商家名"),primary_key=True)
    ID = Column(String(desc="货号"),primary_key=True)
    Url = Column(String(desc="抓取链接"))
    ThumbUrl = Column(String(desc="样图链接"))
    DebutTime = Column(String(desc="发布时间"))
    Title = Column(String(desc="货号"))
    Price = Column(String(desc="价格"))
    Views = Column(Integer(desc="人气"))
    Date = Column(String(desc="更新情况"))
    Insoles = Column(String(desc="鞋垫"))
    Brand = Column(String(desc="品牌"))
    HeadStyle = Column(String(desc="鞋头款式"))
    CloseStyle = Column(String(desc="闭合方式"))
    SoleMaterial = Column(String(desc="鞋底材质"))
    FaceMaterial = Column(String(desc="鞋面材质"))
    InnerFaceMaterial = Column(String(desc="鞋面内里材质"))
    AssembleMethod = Column(String(desc="制作工艺"))
    HeelStyle = Column(String(desc="跟底款式"))
    HeelHeight = Column(String(desc="跟底"));
    Pattern = Column(String(desc="样式"))
    StylishElements = Column(String(desc="流行元素"))
    Style= Column(String(desc="风格"))
    StyleDetails= Column(String(desc="细分风"))
    Scene= Column(String(desc="场合"))
    Season = Column(String(desc="季节"))
    Colors = Column(String(desc="颜色分类 "))
    Sizes = Column(String(desc="尺码"))
    SheosType = Column(String(desc="款式"))
    Functionality = Column(String(desc="功能"))
    Subjects = Column(String(desc="适用对象"))
    PreviewURLs = Column(String(desc="预览链接"))
    GalleryURLs = Column(String(desc="展示链接"))
    MetaData = Column(String(desc="其它数据"))