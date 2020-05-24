import json
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
    headers = {
        # Imitate browser user agent
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36'
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
        if price is None or link['href'] is None or store_id is None:
            raise ListingParsingError()
        listing = Listing(part.element_id, part.color_id, part.qty, price, link.text, link['href'], store_id)
        listings.append(listing)
    return listings


def output_purchase_to_csv(lego_set, purchase, set_id):
    with open(lego_set.bricklink_file, 'w+') as f:
        f.write('part_id,element_id,qty,price,name,link\n')
        for p in purchase:
            f.write(str(p))


if __name__ == '__main__':
    # try:
    #     set_id = sys.argv[1]
    # except:
    #     set_id = '75102-1'
    # lego_set = create_setlist(set_id)
    # to_buy = optimize_bricklink(lego_set)
    # output_purchase_to_csv(lego_set, to_buy, set_id)
    listings = []
    parts = load_parts('data/tetresque.xml')
    for part in parts:
        listings.extend(get_part_listings(part))
    store_ids = set()
    for listing in listings:
        store_ids.add(listing.store_id)
    stores = []
    for store_id in store_ids:
        stores.append(Store(store_id))
    optimize(parts, listings, stores)
