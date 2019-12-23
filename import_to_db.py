import json
import os
import re
import sys
import importlib

from data_model_base import (
    import_data_model,
    is_primary_key,
    get_tables_list,
)

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.inspection import inspect
from sqlalchemy.exc import OperationalError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from os import listdir
from os.path import isfile, join


db_path = "stock.db"
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

def main():


    # each directory under tables repersent a table
    tables_names_list = [
        dir_name for dir_name in os.listdir("tables")
        if os.path.isdir(os.path.join("tables", dir_name)) and
        not dir_name.startswith("__")
    ]
    #if (len(sys.argv) > 2):
    #  db_path = sys.argv[2]
    engine = create_engine('sqlite:///{}'.format(db_path),connect_args={'timeout': 3600})

    if (sys.argv[0] == "all"):
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

main()
