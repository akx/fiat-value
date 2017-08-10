from decimal import Decimal
from xml.etree.ElementTree import fromstring

import requests

from fiatvalue.call_cacher import Cache

rate_cache = Cache('rates', ttl=43200)


@rate_cache.wrap_function
def get_eur_rates():
    rates = {}
    resp = requests.get('https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml')
    resp.raise_for_status()
    tree = fromstring(resp.text)
    for node in tree.findall('.//{http://www.ecb.int/vocabulary/2002-08-01/eurofxref}Cube'):
        currency = node.get('currency')
        rate = node.get('rate')
        if currency and rate:
            rates[currency] = Decimal(rate)
    return rates


def convert_eur_to(value, other_currency):
    rate = get_eur_rates()[other_currency]
    return value * rate
