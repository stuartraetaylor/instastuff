#!/usr/bin/env python3

import argparse
import logging
import requests
import json
import re
import time
import math

logging.basicConfig(level=logging.INFO)

request_params = [{
    'name': 'following',
    'edge': 'edge_follow',
    'query': 'd04b0a864b4b54837c0d870b0e77e076',
},{
    'name': 'followers',
    'edge': 'edge_followed_by',
    'query': 'c76146de99bb02f6415203be841dd25a',
}]

page_size = 50

def _request(user_id, session_id, query_hash, edge_name, startId = ''):
    variables = json.dumps({
        'id': user_id,
        'include_reel': 'false',
        'fetch_mutual': 'false',
        'first': page_size,
        'after': startId,
    })

    uri = 'https://www.instagram.com/graphql/query/'
    cookies = { 'sessionid': session_id }
    params = {
        'variables': variables,
        'query_hash': query_hash,
    }

    r = requests.get(uri, params=params, cookies=cookies)
    logging.debug(r.text)

    if (r.status_code != 200):
        logging.debug("Error: %s", r.text);
        raise RuntimeError('Request failed; status: ' + str(r.status_code))

    r_json = r.json()
    result = r_json['data']['user'][edge_name]
    usernames = []

    for edge in result['edges']:
        username = edge['node']['username']

        logging.debug(username)
        usernames.append(username)

    return {
        'usernames': usernames,
        'count': result['count'],
        'page_info': result['page_info'],
    }

def _fetch_all(user_id, session_id, request_params):
    query_hash = request_params['query']
    edge_name = request_params['edge']
    
    result = _request(user_id, session_id, query_hash, edge_name)

    usernames = result['usernames']
    hasNext = result['page_info']['has_next_page']
    nextPageId = result['page_info']['end_cursor']

    count = result['count']
    total_pages = math.ceil(count / page_size)

    logging.info('Found %s users', count)

    if total_pages > 1:
        pages = total_pages - 1
        logging.info('Loading remaining %s pages ...', pages)

    while hasNext:
        logging.info('Loading next page')
        time.sleep(0.5)

        result = _request(user_id, session_id, query_hash, edge_name, nextPageId)

        usernames += result['usernames']
        hasNext = result['page_info']['has_next_page']
        nextPageId = result['page_info']['end_cursor']

    return usernames

def fetch_users(user_id, session_id):
    usernames = {}

    for params in request_params:
        logging.info('Fetching instagram users: %s', params['name'])
        users = _fetch_all(user_id, session_id, params)

        logging.info('Collected %s users', len(users))
        users.sort()

        usernames[params['name']] = users

    return usernames

def write_users(user_id, session_id):
    usernames = fetch_users(user_id, session_id)

    for key in usernames.keys():
        filename = key + '.txt'
        users = usernames[key]

        logging.info('Writing to file: %s', filename)
        with open(filename, mode='wt', encoding='utf-8') as f:
            f.write('\n'.join(users))

    logging.info('Done, maybe.')

