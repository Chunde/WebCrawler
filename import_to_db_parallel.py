import json
import os
import re
import sys
import importlib
import threading
import multiprocessing
import random

from multiprocessing import Process,Queue,Array,RLock

from data_model_base import (
    import_data_model,
    is_primary_key,
    get_tables_list,
)

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import OperationalError
from sqlalchemy import create_engine
from sqlalchemy.inspection import inspect

from sqlalchemy.orm import sessionmaker
from os import listdir
from os.path import isfile, join

_debug_ = False
db_path = "ShoesMarket.db"
if (len(sys.argv) > 2):
    db_path = sys.argv[2]
engine = create_engine('sqlite:///{}'.format(db_path),connect_args={'timeout': 3600})
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
def import_to_db_worker(id,data_model, onlyfiles):
    n = 0
    engine.dispose()
    #with engine.connect() as conn:
    Session = sessionmaker(bind=engine)
    session = Session()


    for file_name in onlyfiles:
        abs_file_name = join(data_model.json_files_path, file_name)
        unique_dic = {}
        try:
            with open(abs_file_name, 'r',encoding = 'utf-8') as f:
                print(id.__str__() + ":\timporting " + abs_file_name)
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
                n = n + 1
            session.commit()
            print(id.__str__() + ":\t" + abs_file_name + " imported(" + n.__str__() + "/" + len(onlyfiles).__str__() + ")")
        except:
            #os.remove(abs_file_name)
            continue

def import_to_db_parallel(data_model, files):
    key_size = len(files)
    thread_count = multiprocessing.cpu_count()
    random.shuffle(files)
    if thread_count < 1:
       thread_count = 1

    if _debug_:
        thread_count = 1
    key_block_size = int(key_size / thread_count)
    key_block_res = key_size % thread_count
    index = 0
    thread_list = []
    if thread_count > 1:
        for i in range(thread_count):
            block_size = key_block_size
            if i < key_block_res:
                block_size = block_size + 1
            sub_files_list = files[index:index + block_size]
            t = Process(target=import_to_db_worker, args =[i,data_model, sub_files_list]) # a process works much faster than a thread.
            index = index + block_size
            thread_list.append(t)
        for i in range(len(thread_list)):
            thread_list[i].start()
        for i in range(len(thread_list)):# wait for all process
            thread_list[i].join()
    else:
        import_to_db_worker(0,data_model,files)
def import_to_db(engine, data_model):
    # drop the orignal table
    try:
        data_model.__table__.drop(engine);
    except OperationalError:
        pass
    data_model.base.metadata.create_all(engine)
    onlyfiles = [f for f in listdir(data_model.json_files_path) if isfile(join(data_model.json_files_path, f))]

    return import_to_db_parallel(data_model,onlyfiles)
    
def main():

    # each directory under tables repersent a table
    tables_names_list = [
        dir_name for dir_name in os.listdir("tables")
        if os.path.isdir(os.path.join("tables", dir_name)) and
        not dir_name.startswith("__")
    ]
    if (sys.argv[1] == "all"):
        for table_name in tables_names_list:
            data_model = import_data_model(table_name)
            import_to_db(engine, data_model)
    else:
        table_name = sys.argv[1]
        if table_name not in tables_names_list:
            print("wrong table names {}".format(table_name))
        else:
            data_model = import_data_model(table_name)
            import_to_db(engine, data_model)


if __name__ == '__main__':
   

    main()
