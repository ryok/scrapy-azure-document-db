# -*- coding: utf-8 -*-

import re
import xlrd
import json
import collections as cl
import pydocumentdb
import pydocumentdb.document_client as document_client

config = { 
    'ENDPOINT': 'https://scraping-pool-documentdb.documents.azure.com:443/',
    'MASTERKEY': 'XSgJ6wV0b6a6vIpOf4aAHKvvgWRVRP78FgtKGRS83GIHokyKCRvaadkOARGVHUFXlsJfuZDWplpOGdpSzOqUzg==',
    'DOCUMENTDB_DATABASE': 'scraping-book',
    'DOCUMENTDB_COLLECTION_FROM': 'market-operations',
    'DOCUMENTDB_COLLECTION_TO': 'market-operations-cleansed',
};


def selectFromDocmentDb():

    date_list = []
    brand_type_list = []
    remaining_years_list = []
    price_list = []
    price_add_count = 0

    # Initialize the Python DocumentDB client
    client = document_client.DocumentClient(config['ENDPOINT'], {'masterKey': config['MASTERKEY']})
    # create a database if not yet created
    database_definition = {'id': config['DOCUMENTDB_DATABASE'] }
    databases = list(client.QueryDatabases({
            'query': 'SELECT * FROM root r WHERE r.id=@id',
            'parameters': [
                { 'name':'@id', 'value': database_definition['id'] }
            ]
        }))
    if ( len(databases) > 0 ):
        db = databases[0]
    else:
        print ("database is not found:%s" % config['DOCUMENTDB_DATABASE'])

    # Create collection options
    options = {
        'offerEnableRUPerMinuteThroughput': True,
        'offerVersion': "V2",
        'offerThroughput': 400
    }
    # create a collection if not yet created
    collection_definition = { 'id': config['DOCUMENTDB_COLLECTION_FROM'] }
    collections = list(client.QueryCollections(
        db['_self'],
        {
            'query': 'SELECT * FROM root r WHERE r.id=@id',
            'parameters': [
                { 'name':'@id', 'value': collection_definition['id'] }
            ]
        }))
    if ( len(collections) > 0 ):
        collection = collections[0]
    else:
        print ("collection is not found:%s" % config['DOCUMENTDB_COLLECTION_FROM'])

    # search documents
    condition_list = []
    documents = list(client.QueryDocuments(
        collection['_self'],
        {
            'query': 'SELECT * FROM c'
        }))
    if (len(documents) < 1):
        print ("document is not found")
    else:
        for doc in documents:
            for item in doc['offer']:
                if price_add_count != 0:
                    i = 0
                    while i < price_add_count:
                        price_list.append(item)
                        i += 1
                    price_add_count = 0
                else:
                    pattern = r"国債買入"
                    matchOB = re.match(pattern, item)
                    if matchOB:
                        if "国債買入（変動利付債）" == item:
                            date_list.append(doc['date'])
                            brand_type_list.append('変動利付債')
                            remaining_years_list.append('-')
                            condition_list.append(item)
                            price_add_count += 1
                        elif "国債買入（残存期間３年超５年以下）" == item:
                            for num in [3,4,5]:
                                date_list.append(doc['date'])
                                brand_type_list.append('normal')
                                remaining_years_list.append(num)
                                condition_list.append(item)
                                price_add_count += 1
                        elif "国債買入（残存期間１年超３年以下）" == item:
                            for num in [1,2,3]:
                                date_list.append(doc['date'])
                                brand_type_list.append('normal')
                                remaining_years_list.append(num)
                                condition_list.append(item)
                                price_add_count += 1
                        elif "国債買入（残存期間２５年超）" == item:
                            for num in range(25, 100):
                                date_list.append(doc['date'])
                                brand_type_list.append('normal')
                                remaining_years_list.append(num)
                                condition_list.append(item)
                                price_add_count += 1
                        elif "国債買入（残存期間１０年超２５年以下）" == item:
                            for num in range(10, 25):
                                date_list.append(doc['date'])
                                brand_type_list.append('normal')
                                remaining_years_list.append(num)
                                condition_list.append(item)
                                price_add_count += 1
                        elif "国債買入（物価連動債）" == item:
                            date_list.append(doc['date'])
                            brand_type_list.append('物価連動債')
                            remaining_years_list.append('-')
                            condition_list.append(item)
                            price_add_count += 1
                        elif "国債買入（残存期間１年以下）" == item:
                            for num in [0,1]:
                                date_list.append(doc['date'])
                                brand_type_list.append('normal')
                                remaining_years_list.append(num)
                                condition_list.append(item)
                                price_add_count += 1
                        elif "国債買入（残存期間５年超１０年以下）" == item:
                            for num in range(5, 10):
                                date_list.append(doc['date'])
                                brand_type_list.append('normal')
                                remaining_years_list.append(num)
                                condition_list.append(item)
                                price_add_count += 1
                        elif "国債買入（固定利回り方式）（残存期間５年超１０年以下）" == item:
                            for num in range(5, 10):
                                date_list.append(doc['date'])
                                brand_type_list.append('固定利回り方式')
                                remaining_years_list.append(num)
                                condition_list.append(item)
                                price_add_count += 1
                        else:
                            print ('Unexpected condtion found!:%s' % item)
    
    dict4store = []
    for i in range(len(date_list)):
        data = cl.OrderedDict()
        if date_list[i]:
            data['date'] = date_list[i]
            data['brand_type'] = brand_type_list[i]
            data['remaining_years'] = remaining_years_list[i]
            data['price'] = price_list[i]
            data['condition'] = condition_list[i]
            dict4store.append(data)
    store2DocmentDb(dict4store)
    #condition_list_uq = list(set(condition_list))
    #print (condition_list_uq)


def store2DocmentDb(dict4store):
    # Initialize the Python DocumentDB client
    client = document_client.DocumentClient(config['ENDPOINT'], {'masterKey': config['MASTERKEY']})
    # create a database if not yet created
    database_definition = {'id': config['DOCUMENTDB_DATABASE'] }
    databases = list(client.QueryDatabases({
            'query': 'SELECT * FROM root r WHERE r.id=@id',
            'parameters': [
                { 'name':'@id', 'value': database_definition['id'] }
            ]
        }))
    if ( len(databases) > 0 ):
        db = databases[0]
    else:
        print ("database is created:%s" % config['DOCUMENTDB_DATABASE'])
        db = client.CreateDatabase(database_definition)

    # Create collection options
    options = {
        'offerEnableRUPerMinuteThroughput': True,
        'offerVersion': "V2",
        'offerThroughput': 400
    }
    # create a collection if not yet created
    collection_definition = { 'id': config['DOCUMENTDB_COLLECTION_TO'] }
    collections = list(client.QueryCollections(
        db['_self'],
        {
            'query': 'SELECT * FROM root r WHERE r.id=@id',
            'parameters': [
                { 'name':'@id', 'value': collection_definition['id'] }
            ]
        }))
    if ( len(collections) > 0 ):
        collection = collections[0]
    else:
        print ("collection is created:%s" % config['DOCUMENTDB_COLLECTION_TO'])
        collection = client.CreateCollection(db['_self'], collection_definition, options)

    # Create some documents
    for entry in dict4store:
        data = {
            'key':entry['date'] + '@' + str(entry['remaining_years']),
            'date':entry['date'],
            'brand_type':entry['brand_type'],
            'remaining_years':entry['remaining_years'],
            'price':entry['price'],
            'condition':entry['condition']
        }
        # check if duplicated
        documents = list(client.QueryDocuments(
            collection['_self'],
            {
                'query': 'SELECT * FROM root r WHERE r.key=@key',
                'parameters': [
                    { 'name':'@key', 'value':data['key'] }
                ]
            }))
        if (len(documents) < 1):
            # only create if it's fully new document
            print ("document is added:key: %s" % data['key'])
            created_document = client.CreateDocument(
                    collection['_self'], data)


if __name__ == '__main__':
    selectFromDocmentDb()