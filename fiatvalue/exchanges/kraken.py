import base64
import hashlib
import hmac
import time
from decimal import Decimal
from collections import defaultdict
from urllib.parse import urlencode, urlparse

from fiatvalue.exchanges.base import BaseAPI


class KrakenAPI(BaseAPI):
    url_format = 'https://api.kraken.com/0/{endpoint}'
    id = 'kraken'

    def _sign_request(self, request_args, params):
        if not (self.api_key and self.api_secret):
            raise ValueError('API key and/or secret not initialized')
        params = dict(params, nonce=int(1000*time.time()))
        post_data = urlencode(params)
        encoded = ('%s%s' % (params['nonce'], post_data)).encode()
        message = urlparse(request_args['url']).path.encode() + hashlib.sha256(encoded).digest()
        signature = hmac.new(base64.b64decode(self.api_secret), message, hashlib.sha512)
        sigdigest = base64.b64encode(signature.digest()).decode()
        request_args['headers'].update({'API-Key': self.api_key, 'API-Sign': sigdigest})
        return post_data

    def query_private(self, endpoint, params={}):
        return self.call(endpoint='private/%s' % endpoint, params=params, post=True, sign=True)

    def query_public(self, endpoint, params={}):
        return self.call(endpoint='public/%s' % endpoint, params=params, post=False)

    def get_order_prices_and_vols(self, fiat='USD'):
        orders = self.query_private('ClosedOrders')

        buy_prices_and_vols = defaultdict(list)
        sell_prices_and_vols = defaultdict(list)

        for id, order in orders['result']['closed'].items():
            order_d = order['descr']
            coin = order_d['pair'][:3]
            o_fiat = order_d['pair'][3:]
            if fiat != o_fiat:
                continue
            price = Decimal(order['price'])
            qty = Decimal(order['vol_exec'])
            if order_d['type'] == 'buy':
                buy_prices_and_vols[coin].append((price, qty))
            elif order_d['type'] == 'sell':
                sell_prices_and_vols[coin].append((price, qty))
            else:
                raise NotImplementedError('...', order)

        return {
            'buy': buy_prices_and_vols,
            'sell': sell_prices_and_vols,
        }


    def get_balances(self):
        balances = self.query_private('Balance')['result']
        return {asset[-3:]: Decimal(value) for (asset, value) in balances.items()}

    def get_ticker(self, coins, fiat='USD'):
        pairs = ['%s%s' % (coin, fiat) for coin in coins if coin not in ('EUR', 'USD', fiat)]
        values = {}
        for pair, info in self.query_public('Ticker', {'pair': ','.join(pairs)})['result'].items():
            assert pair.endswith(fiat)
            if len(pair) == 8:
                coin = pair[1:4]
            elif len(pair) == 6:
                coin = pair[0:3]
            else:
                raise ValueError(pair)
            values[coin] = Decimal(info['o'])
        return values
