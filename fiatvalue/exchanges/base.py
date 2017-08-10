import requests

from fiatvalue.excs import APIError


class BaseAPI:
    url_format = None

    def __init__(self, client_id, api_key, api_secret):
        self.client_id = client_id
        self.api_key = api_key
        self.api_secret = api_secret

    def _sign_request(self, request_args, params):
        raise NotImplementedError('...')

    def call(self, endpoint, *, post=False, params=None, sign=False):
        request_args = {
            'method': ('post' if post else 'get'),
            'url': self.url_format.format(endpoint=endpoint.strip('/')),
            'headers': {},
        }
        if params is None:
            params = {}
        if sign:
            params = self._sign_request(request_args, params)
        request_args[('data' if request_args['method'] == 'post' else 'params')] = params
        resp = requests.request(**request_args)
        if resp.status_code >= 400:
            raise APIError(resp.content, response=resp)
        data = resp.json()
        if isinstance(data, dict) and data.get('error'):
            raise APIError(data['error'], response=resp)
        return data

    def get_order_prices_and_vols(self, fiat='USD'):
        raise NotImplementedError('...')

    def get_balances(self):
        raise NotImplementedError('...')

    def get_ticker(self, coins, fiat='USD'):
        raise NotImplementedError('...')
