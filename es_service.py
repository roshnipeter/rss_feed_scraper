from datetime import datetime, timedelta
import os
from elasticsearch import helpers, Elasticsearch
import yaml
import config

es = Elasticsearch(config.config['es_host'])

def get_data(index, query):
    '''
    Returns the data from the given ES index
    params: 
        index - es index name
        query - query for ES search
    '''
    total_count = 0
    result_list = []
    for es_doc in helpers.scan(client=es, query=query, index=index, size=2000, scroll="5s"):
        result_list.append(es_doc["_source"])
        total_count += 1
    return (result_list, total_count)

def add_data(index, es_obj):
    '''
    Indexes the data to given ES index
    params: 
        index - es index name
        es_obj - document for ES
    '''
    try:
        es.index(index = index, body = es_obj)
        return {"success":True, "message":"Record added successfully!"}
    except:
        return {"success":False, "message":"Record not added."} 
