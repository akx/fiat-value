import base64
import hashlib
import hmac
import time
from urllib.parse import urlencode, urlparse

import requests


class APIError(Exception):
    def __init__(self, message, response):
        super(APIError, self).__init__(message)
        self.response = response


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


class BitstampAPI(BaseAPI):
    url_format = 'https://www.bitstamp.net/api/v2/{endpoint}/'

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


# noinspection PyDefaultArgument
class KrakenAPI(BaseAPI):
    url_format = 'https://api.kraken.com/0/{endpoint}'

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
