import json
import os
import re
import importlib

from datetime import date

from sqlalchemy.inspection import inspect
from sqlalchemy import Column as _Column
from sqlalchemy import Float as _Float
from sqlalchemy import Integer as _Integer
from sqlalchemy import String as _String
from sqlalchemy import Date as _Date


def is_primary_key(column, data_model):
    return column in inspect(data_model).primary_key

class ProcessFail(Exception):
    pass


class BaseAttribute:
    def parse_money_field(self, field):
        # e.g. 174亿

        # serch for real number
        regex = re.search(r"[-+]?\d*\.\d+|\d+", field)
        # number = 174
        number = float(regex.group())
        # unit = 亿
        unit = field[regex.span()[1]:]
        if unit =='' or unit == '元':
            return number
        elif unit == '亿':
            return number * 1e8
        elif unit == '万':
            return number * 1e4
        elif unit == '万亿':
            return number * 1e12
        else:
            raise ProcessFail(
                "Unrecognized field {} for {}".format(field, self.description))


def default_decorator(process_func):
    def new_process_func(cls, field):
        if not field:
            return None
        if field == "--":
            return None
        field = field.replace(",", "")
        return process_func(cls, field)
    return new_process_func


class Float(_Float, BaseAttribute):
    def __init__(self, *args, **kwargs):
        self.description = kwargs.pop('desc', "")
        self.unit = kwargs.pop('unit', "")
        super().__init__(*args, **kwargs)

    @default_decorator
    def preprocess(self, field):
        return float(self.parse_money_field(field))

class Percentage(_Float, BaseAttribute):
    def __init__(self, *args, **kwargs):
        self.description = kwargs.pop('desc', "")
        self.unit = kwargs.pop('unit', "%")
        super().__init__(*args, **kwargs)

    @default_decorator
    def preprocess(self, field):
        return float(field.strip("%"))


class Integer(_Integer, BaseAttribute):
    def __init__(self, *args, **kwargs):
        self.description = kwargs.pop('desc', "")
        self.unit = kwargs.pop('unit', "")
        super().__init__(*args, **kwargs)

    @default_decorator
    def preprocess(self, field):
        return int(self.parse_money_field(field))


class String(_String, BaseAttribute):
    def __init__(self, *args, **kwargs):
        self.description = kwargs.pop('desc', "")
        self.unit = kwargs.pop('unit', "")
        super().__init__(*args, **kwargs)

    @default_decorator
    def preprocess(self, field):
        return field

class Date(_Date, BaseAttribute):
    def __init__(self, *args, **kwargs):
        self.description = kwargs.pop('desc', "")
        self.unit = kwargs.pop('unit', "")
        super().__init__(*args, **kwargs)

    @default_decorator
    def preprocess(self, field):
        # can relax later

        # for 2014-03-20 or 2014-3-20
        result = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})$", field)

        def temp1(field_tuple):
            assert len(field_tuple) == 3
            year, month, day = tuple(int(number) for number in field_tuple)
            return date(year, month, day)

        def temp2(field_tuple):
            assert len(field_tuple) == 3
            year, month, day = tuple(int(number) for number in field_tuple)
            year += 2000
            return date(year, month, day)

        def temp3(field_tuple):
            assert len(field_tuple) == 1
            year = int(field_tuple[0])
            return date(year, 1, 1)

        def temp4(field_tuple):
            return None

        regular_expressions = {
            r"^(\d{4})-(\d{1,2})-(\d{1,2})$": temp1,
            r"^(\d{2})-(\d{1,2})-(\d{1,2})$": temp2,
            r"^(\d{4})$": temp3,
            r"^总计$": temp4
        }
        for reg_ex, func in regular_expressions.items():
            result =  re.match(reg_ex, field)
            if result:
                return func(result.groups())

        raise ProcessFail("fail to parse date {}".format(field))

class Column(_Column):
    def __init__(self, *args, **kwargs):
        self.type = args[0]
        # self.名称 = self.type.description
        # self.单位 = self.type.unit
        # TODO check type is subclass of BaseAttribute
        super().__init__(*args, **kwargs)

    def preprocess(self, field):
        return self.type.preprocess(field)

    def 名称(self):
        return self.type.description

    def 单位(self):
        return self.type.unit

def import_data_model(table_name):
    # e.g. "sharedholder_top_holder -> SharedholderTopHolder"
    #class_name = "".join([word.title() for word in table_name.split("_")])
    class_name = table_name
    print("importing {} from {}".format(class_name, table_name))

    return getattr(
        # dynamically import module
        importlib.import_module("Tables.{}.data_model".format(table_name)),
        class_name
    )


def get_tables_list():
    return [
        dir_name for dir_name in os.listdir("Tables")
        if os.path.isdir(os.path.join("Tables", dir_name)) and
        not dir_name.startswith("__")
    ]
