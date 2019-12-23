import json
from json import dumps
import os
from os.path import join
from multiprocessing import Process,Queue,Array,RLock,Lock
import multiprocessing
import threading
from Macro import _use_local_dealer_list_, _debug_,_max_thread_

def ParallelAgent(index_list, worker_method, thread_count = None):
    key_size = len(index_list)
    if not thread_count:
        thread_count = multiprocessing.cpu_count()
        if thread_count < 1:
           thread_count = 1
    key_block_size = 1
    key_block_res = 0
    #thread_count = 3
    if key_size > thread_count:
        key_block_size = int(key_size / thread_count)
        key_block_res = key_size % thread_count
    else:
        thread_count = key_size
    if _debug_:
        thread_count = 1

    index = 0
    thread_list = []
    if thread_count > 1:
        for i in range(thread_count):
            block_size = key_block_size
            if i < key_block_res:
                block_size = block_size + 1
            sub_stock_list = index_list[index:index + block_size]
            t = threading.Thread(target=worker_method, args =[sub_stock_list]) # a process works much faster than a thread.
            index = index + block_size
            thread_list.append(t)
        for i in range(len(thread_list)):
           thread_list[i].start()
        for i in range(len(thread_list)):# wait for all process
            thread_list[i].join()
    else:
        worker_method(index_list)
    print("Parallel Agent [{}] Exits..".format(worker_method.__name__))

