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

def save_to_DB(data, session, data_model):
    try:
        session.merge(data_model(**data))
        #session.commit()
        #print(data)
    except  BaseException as e:
        print(str(e))

def object_as_dict(obj):
    return {c.key: getattr(obj, c.key)
            for c in inspect(obj).mapper.column_attrs}

if __name__ == '__main__':
    src_engine = create_engine('sqlite:///{}'.format("../b/e.db"),connect_args={'timeout': 1})
    dst_engine = create_engine('sqlite:///{}'.format("../b/Database.db"),connect_args={'timeout': 1})
    data_model = import_data_model('ShoesDescriptor')

    data_model.base.metadata.create_all(src_engine)
    SSession = sessionmaker(bind=src_engine)
    DSession = sessionmaker(bind=dst_engine)
    ssession = SSession()
    dsession = DSession()
    ssession.text_factory = bytes
    items = ssession.query(data_model).all()
    ditems = dsession.query(data_model).all()
    print(len(items))
   # print(len(ditems))
    for item in items:
        dic = object_as_dict(item)
       # print(dic)
        save_to_DB(dic,dsession,data_model)
    dsession.commit()
    dsession.close()
    ssession.close()

