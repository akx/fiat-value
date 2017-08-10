import hashlib
import hmac
import time

from fiatvalue.exchanges.base import BaseAPI


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


