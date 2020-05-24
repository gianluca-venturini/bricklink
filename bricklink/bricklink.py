import argparse
import json
import re
import sys
from collections import Counter
from copy import copy
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup as soup

from db import load_parts
from models import Listing, Part, Store
from optimization import optimize


class PartNotFoundError(Exception):

    def __init__(self, part):
        self.part = part


class ListingParsingError(Exception):
    pass


class QuotaExceededError(Exception):
    pass


headers = {
    # Imitate browser user agent
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36'
}


def get_part_listings(part):
    print('fetching listings for part', part)
    listings = []
    url = 'http://www.bricklink.com/search.asp'
    params = {
        'viewFrom': 'sf',
        'qMin': part.qty,
        'colorID': part.color_id,
        'shipCountryID': 'US',
        'sellerCountryID': 'US',
        'moneyTypeID': 1,
        'w': part.element_id,
        # 'sellerLoc': 'C',
        'searchSort': 'P',
        'sz': 5
    }
    html = requests.get(url, headers=headers, params=params).text
    if 'Quota Exceeded' in html:
        raise QuotaExceededError()
    results = soup(html, 'html.parser').findAll('td', {'valign' : 'TOP'})
    if len(results) == 0:
        raise PartNotFoundError(part)
    for r in results:
        link = r.find('a')
        price = r.findAll('b')[1].text
        price = float(price.replace('US $', ''))
        store_id = parse_qs(urlparse(link['href']).query)['p'][0]
        inventory_id = int(parse_qs(urlparse(link['href']).query)['itemID'][0])
        if price is None or link['href'] is None or store_id is None:
            raise ListingParsingError()
        listing = Listing(part.element_id, part.color_id, part.qty, price, link.text, link['href'], store_id, inventory_id)
        listings.append(listing)
    return listings


def output_purchase_to_csv(lego_set, purchase, set_id):
    with open(lego_set.bricklink_file, 'w+') as f:
        f.write('part_id,element_id,qty,price,name,link\n')
        for p in purchase:
            f.write(str(p))


def get_listings(xml_file):
    listings = []
    parts = load_parts(xml_file)
    for part in parts:
        listings.extend(get_part_listings(part))
    store_ids = set()
    for listing in listings:
        store_ids.add(listing.store_id)
    stores = []
    for store_id in store_ids:
        stores.append(Store(store_id))
    return parts, stores, listings


def insert_in_cart(listings):
    for listing in listings:
        html = requests.get(listing.link, headers=headers).text
        # id: 			442292,
        p = re.compile('id:[^\d]+(\d+),')
        seller_id = int(p.search(html).group(1))
        params = {
            'itemArray': json.dumps([{
                'invID': listing.inventory_id,
                'invQty': listing.qty,
                'sellerID': seller_id,
                'sourceType': 1 # Magic number
            }]),
            'srcLocation': 1100, # Magic number
            'sid': seller_id,
        }
        cookies = {
            'cartBuyerID': '-699031000',
        }
        print('adding itemArray {itemArray}'.format(**params), ' to cartBuyerID {cartBuyerID}'.format(**cookies))
        html = requests.post('https://store.bricklink.com/ajax/clone/cart/add.ajax', params=params, headers=headers, cookies=cookies).text
        print(html)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Optimize Bricklink buying process.')
    parser.add_argument('--cart', help='the cartBuyerID cookie')
    parser.add_argument('--buy', help='Creates carts for you', action='store_true')
    args = parser.parse_args()

    if args.buy is True and args.cart is None:
        print('Error, specify --cart')
        exit(1)

    parts, stores, listings = get_listings('data/test.xml')
    optimal_listings = optimize(parts, listings, stores)
    insert_in_cart(optimal_listings)
