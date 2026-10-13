"""Bounded, server-only PayMongo API transport. Never retries a mutation."""
import base64
import http.client
import json
import re
import socket
import urllib.error
import urllib.request
from django.conf import settings


class ProviderError(Exception):
    def __init__(self, message='Payment provider unavailable.', uncertain=False, retryable=True):
        super().__init__(message)
        self.uncertain = uncertain
        self.retryable = retryable


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class _HTTPSConnection(http.client.HTTPSConnection):
    def connect(self):
        super().connect()
        self.sock.settimeout(getattr(settings, 'PAYMONGO_READ_TIMEOUT', 15))


class _HTTPSHandler(urllib.request.HTTPSHandler):
    def https_open(self, req):
        return self.do_open(_HTTPSConnection, req, context=self._context)


class PayMongoClient:
    BASE_URL = 'https://api.paymongo.com/v1/'

    def __init__(self, mode=None):
        self.mode = mode or getattr(settings, 'PAYMONGO_MODE', 'test')
        key = getattr(settings, 'PAYMONGO_SECRET_KEY_' + self.mode.upper(), '') or getattr(settings, 'PAYMONGO_SECRET_KEY', '')
        if self.mode not in ('test', 'live') or not key.startswith('sk_' + self.mode + '_'):
            raise ProviderError('PayMongo secret key does not match checkout mode.', retryable=False)
        self.authorization = 'Basic ' + base64.b64encode((key + ':').encode()).decode()
        self.opener = urllib.request.build_opener(_NoRedirect(), _HTTPSHandler())

    def _request(self, method, path, attributes=None):
        body = None if attributes is None else json.dumps({'data': {'attributes': attributes}}).encode()
        req = urllib.request.Request(self.BASE_URL + path, data=body, method=method,
                                     headers={'Authorization': self.authorization, 'Content-Type': 'application/json',
                                              'Accept': 'application/json'})
        try:
            with self.opener.open(req, timeout=getattr(settings, 'PAYMONGO_CONNECT_TIMEOUT', 5)) as response:
                raw = response.read(4 * 1024 * 1024 + 1)
                if len(raw) > 4 * 1024 * 1024:
                    raise ProviderError(uncertain=method != 'GET')
                result = json.loads(raw)
                if not isinstance(result, dict) or not isinstance(result.get('data'), dict):
                    raise ProviderError(uncertain=method != 'GET')
                return result['data']
        except urllib.error.HTTPError as exc:
            # Provider response body can contain credentials/customer data; never surface it.
            raise ProviderError('PayMongo rejected the request.', uncertain=method != 'GET' and exc.code >= 500, retryable=exc.code >= 500) from None
        except (urllib.error.URLError, socket.timeout, TimeoutError, OSError, ValueError, http.client.HTTPException) as exc:
            raise ProviderError(uncertain=method != 'GET') from None

    @staticmethod
    def _id(value):
        if not re.fullmatch(r'[A-Za-z0-9_]+', value or ''):
            raise ProviderError('Invalid provider resource identifier.')
        return value

    def create_intent(self, attempt):
        return self._request('POST', 'payment_intents', {
            'amount': attempt.amount_centavos, 'currency': 'PHP', 'payment_method_allowed': ['qrph'],
            'description': 'GyMMS ' + str(attempt.pk), 'metadata': {'attempt_id': str(attempt.pk)}})

    def create_method(self, attempt):
        expiry = getattr(settings, 'PAYMONGO_QR_EXPIRY_SECONDS', 1800)
        return self._request('POST', 'payment_methods', {'type': 'qrph', 'expiry_seconds': max(60, min(9000, expiry))})

    def attach_method(self, intent_id, method_id):
        return self._request('POST', 'payment_intents/' + self._id(intent_id) + '/attach',
                             {'payment_method': self._id(method_id)})

    def retrieve_intent(self, intent_id):
        return self._request('GET', 'payment_intents/' + self._id(intent_id))

    def retrieve_payment(self, payment_id):
        return self._request('GET', 'payments/' + self._id(payment_id))

    def cancel_intent(self, intent_id):
        return self._request('POST', 'payment_intents/' + self._id(intent_id) + '/cancel', {})
