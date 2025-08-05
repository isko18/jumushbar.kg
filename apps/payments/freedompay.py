# clients/freedompay.py

import hashlib
import random
import string
import requests


class FreedomPayClient:
    MERCHANT_ID = '47598'  # замените на ваш ID
    SECRET_KEY = 'euI03V5l5W7IlFJv'  # замените на ваш секрет
    BASE_URL = 'https://api.freedompay.kg/init_payment.php'

    @classmethod
    def _generate_salt(cls):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=16))

    @classmethod
    def _generate_signature(cls, params: dict):
        sorted_items = sorted(params.items())
        sign_data = ';'.join([str(value) for _, value in sorted_items])
        sign_string = f"init_payment.php;{sign_data};{cls.SECRET_KEY}"
        return hashlib.md5(sign_string.encode()).hexdigest()

    @classmethod
    def create_payment(cls, amount: float, description: str, callback_url: str):
        salt = cls._generate_salt()
        order_id = ''.join(random.choices(string.digits, k=8))

        params = {
            'pg_order_id': order_id,
            'pg_merchant_id': cls.MERCHANT_ID,
            'pg_amount': amount,
            'pg_currency': 'KGS',
            'pg_description': description,
            'pg_salt': salt,
            'pg_result_url': callback_url,
            'pg_success_url': callback_url,
            'pg_failure_url': callback_url,
            'pg_success_url_method': 'GET',
            'pg_failure_url_method': 'GET',
            'pg_testing_mode': 1,
        }

        params['pg_sig'] = cls._generate_signature(params)

        response = requests.post(cls.BASE_URL, files=params)
        response.raise_for_status()

        return {
            'payment_url': response.url,
            'payment_id': order_id,
            'raw_response': response.text,
        }
