# clients/freedompay.py

import hashlib
import random
import string
import requests
import logging

logger = logging.getLogger(__name__)


class FreedomPayClient:
    MERCHANT_ID = '47598'  # замените на ваш ID
    SECRET_KEY = 'euI03V5l5W7IlFJv'  # замените на ваш секрет
    BASE_URL = 'https://api.freedompay.kg/init_payment.php'

    @classmethod
    def _generate_salt(cls):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=16))

    @classmethod
    def _generate_signature(cls, params: dict):
        # Убираем pg_sig, если есть
        params = {k: v for k, v in params.items() if k != 'pg_sig'}

        # Сортировка по ключам (алфавитный порядок)
        sorted_keys = sorted(params.keys())

        # Формирование строки: сначала имя скрипта, потом значения по ключам, потом секретный ключ
        sign_parts = ['init_payment.php']
        for key in sorted_keys:
            sign_parts.append(str(params[key]))
        sign_parts.append(cls.SECRET_KEY)

        sign_string = ';'.join(sign_parts)
        return hashlib.md5(sign_string.encode()).hexdigest()


    @classmethod
    def create_payment(cls, amount: float, description: str, callback_url: str):
        salt = cls._generate_salt()
        order_id = ''.join(random.choices(string.digits, k=8))

        params = {
            'pg_order_id': order_id,
            'pg_merchant_id': '560709',  # ✅ Новый ID от Damir
            'pg_amount': amount,
            'pg_currency': 'KGS',
            'pg_description': description,
            'pg_salt': salt,
            'pg_result_url': callback_url,
            'pg_success_url': 'https://example.com/success',
            'pg_failure_url': 'https://example.com/failure',
            # ❌ НЕ ДОБАВЛЯЕМ:
            # 'pg_success_url_method': 'GET',
            # 'pg_failure_url_method': 'GET',
            # 'pg_testing_mode': 1,
        }


        # 🔽 Строка подписи
        sign_data = ';'.join([str(value) for _, value in sorted(params.items())])
        sign_string = f"init_payment.php;{sign_data};{cls.SECRET_KEY}"
        pg_sig = hashlib.md5(sign_string.encode()).hexdigest()
        params['pg_sig'] = pg_sig

        # 🔽 Логируем всё
        logger.warning("FreedomPay Request Params:")
        for k, v in params.items():
            logger.warning(f"{k} = {v}")
        logger.warning(f"Signature String: {sign_string}")
        logger.warning(f"Generated Signature: {pg_sig}")

        # 🔽 Отправка запроса
        response = requests.post(cls.BASE_URL, files=params)
        response.raise_for_status()

        return {
            'payment_url': response.url,
            'payment_id': order_id,
            'raw_response': response.text,
        }