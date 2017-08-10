import hashlib
import hmac
import re
import time

from collections import defaultdict

from decimal import Decimal

from fiatvalue.exchanges.base import BaseAPI
from fiatvalue.rates import convert_eur_to

CURRENCY_MAP = {'BTC': 'XBT'}
trans_key_re = re.compile(r'^([a-z]{3})_([a-z]{3})$')

def map_currency(currency):
    currency = currency.upper()
    return CURRENCY_MAP.get(currency, currency)


class BitstampAPI(BaseAPI):
    url_format = 'https://www.bitstamp.net/api/v2/{endpoint}/'
    id = 'bitstamp'

    def _sign_request(self, request_args, params):
        if not (self.api_key and self.api_secret):
            raise ValueError('API key and/or secret not initialized')
        nonce = str(int(time.time() * 1e6))
        message = (nonce + self.client_id + self.api_key).encode()
        signature = hmac.new(
            key=self.api_secret.encode(),
            msg=message,
            digestmod=hashlib.sha256,
        ).hexdigest().upper()
        params = dict(params, key=self.api_key, signature=signature, nonce=nonce)
        return params

    def get_balances(self):
        balances = defaultdict(Decimal)
        for key, value in self.call('balance/', post=True, sign=True).items():
            if key.endswith('_balance'):
                coin = map_currency(key.split('_')[0].upper())
                value = Decimal(value)
                if value > 0:
                    balances[coin] += value
        return balances

    def get_order_prices_and_vols(self, fiat='USD'):
        buy_prices_and_vols = defaultdict(list)
        sell_prices_and_vols = defaultdict(list)

        for order in self.call('user_transactions/', params={'limit': 1000}, post=True, sign=True):
            if order['type'] != '2':
                continue
            for key in order:
                m = trans_key_re.match(key)
                if not m:
                    continue
                asset1, asset2 = m.groups()
                value1 = Decimal(order[asset1])
                value2 = Decimal(order[asset2])
                asset1 = map_currency(asset1)
                asset2 = map_currency(asset2)
                assert asset2 in ('EUR', 'USD')  # TODO: maybe get rid of this
                if asset2 == 'EUR':
                    value2 = convert_eur_to(value2, fiat)
                    asset2 = fiat
                assert asset2 == fiat
                rate = abs(value2) / abs(value1)
                if value2 < 0:  # Selling fiat to buy coin
                    buy_prices_and_vols[asset1].append((rate, abs(value1)))
                else:  # Selling coin to buy fiat
                    sell_prices_and_vols[asset1].append((1 / rate, abs(value2)))
        return {
            'buy': buy_prices_and_vols,
            'sell': sell_prices_and_vols,
        }
