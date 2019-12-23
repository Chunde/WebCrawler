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

class ProductSummary(Base):
    base =  Base
    json_files_path = join(current_path, "data")
    __tablename__ = "ProductSummary"

    Dealer = Column(String(desc="商家名称"),primary_key=True)
    SName = Column(String(desc="商品描述"))
    ProductURL = Column(String(desc="商品链接"))
    ImageURL = Column(String(desc="商品图片链接"))
    Price = Column(String(desc="价格"))
    ProductID= Column(String(desc="产品编号"),primary_key=True)
   