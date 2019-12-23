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

class Dealers(Base):
    base =  Base
    json_files_path = join(current_path, "data")
    __tablename__ = "Dealers"

    Name = Column(String(desc="商家名称"),primary_key=True)
    Rating = Column(String(desc="商家链接"))
    URL = Column(String(desc="商家链接"))
    Market = Column(String(desc="市场"))
    Address = Column(String(desc="地址"))
    Phone = Column(String(desc="联系电话"))
    Months = Column(String(desc="入驻时间"))
    URL = Column(String(desc="商家链接"))
    QQ = Column(String(desc="QQ"))
    Products = Column(String(desc="产品数"))
    #Members = Column(String(desc="会员数"))
    #Offlines = Column(String(desc="下架"))
    Initial = Column(String(desc="商家拼音第一个字母"))
    #Origin = Column(String(desc="原始数据"))
