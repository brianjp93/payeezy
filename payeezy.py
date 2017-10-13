"""Python connection to the Payeezy api.

- The direct python wrapper to the payeezy api from Payeezy seems to
be missing some features and I don't like that it sets the api_key,
api_secret, and other values at a module level rather than for an
object. This *probably* won't be a problem for most people but if
you're in a fringe case where you're multi-threading with shared
memory and connecting to different accounts with different api_keys,
then setting attributes at a module level will cause weird bugs
I think.

API endpoint documentation - https://developer.payeezy.com/apis
"""

import os
import requests
import time
from . import http_authorize


class Payeezy(object):

    def __init__(self, api_key, api_secret, token, url, token_url):
        """Initialize Payeezy object.

        Parameters
        ----------
        api_key : str
            Description
        api_secret : str
            Description
        token : str
            Description
        url : str
            live url    - https://api.payeezy.com/v1/transactions
            sandbox url - https://api-cert.payeezy.com/v1/transactions
        token_url : str
            Description
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.token = token
        self.url = url
        self.token_url = token_url

    def make_payload(self, amount=None, currency_code=None, card_type=None,
        cardholder_name=None, card_number=None, card_expiry=None,
        card_cvv=None, description=None, transaction_type=None,
        transaction_tag=None, transaction_id=None, method=None,
        ):
        """
        Parameters
        ----------
        amount : str, optional
            Integer amount - will be coerced to string.
        currency_code : str, optional
            ISO currency code - coerced to uppercase string
        card_type : str, optional
            allowed - `visa`, `mastercard`, `american express`,
            `jcb`, `diners club`, `discover`.
        cardholder_name : str, optional
            Name associated with card.
        card_number : None, optional
            Description
        card_expiry : str, optional
            Card expiration date.
        card_cvv : str, optional
            3 or 4 digit verification code.
        description : None, optional
        transaction_type : str, optional
            `['authorize', 'purchase', 'capture', 'void', 'refund']`
        transaction_tag : str, optional
        transaction_id : str, optional
        method : str, optional
            The method of payment - defaults to `'credit_card'`
        card_number : str, optional
        description : str, optional
        transaction_tag : str, optional
        transaction_id : str, optional
        
        Returns
        -------
        dict
            A dictionary with `payload` and `transaction_id`
        
        Raises
        ------
        ValueError,
            Description
        ValueError,
        """
        if amount is None:
            raise ValueError('amount cannot be None')
        amount = str(amount)
        if currency_code is None:
            raise ValueError('currency_code cannot be None')
        if transaction_type is None:
            raise ValueError('transaction_type cannot be None')
        # TODO : Possibly change this line because I think we can
        #   accept more than just USD...
        if currency_code.upper() != 'USD':
            # we only accept USD? - this was in the Payeezy's original docs
            # but I thought we could accept more...
            raise ValueError('currency code provided is not valid')
        if description is None:
            description = '{} transaction for amount: {}'.format(transaction_type, amount)
        if method is None:
            raise ValueError('method cannot be None')
        if transaction_type in ['authorize', 'purchase']:
            if card_number is None:
                raise ValueError('card number cannot be None')
            card_number = str(card_number)
            if cardholder_name is None:
                cardholder_name = 'Not Provided'
            if card_cvv is None:
                raise ValueError('cvv number cannot be None')
            card_cvv = str(card_cvv)
            if card_expiry is None:
                raise ValueError('card expiration cannot be None.  It has to be in MMYY format')
            card_expiry = str(card_expiry)

            payload = {
                'merchant_ref': description,
                'transaction_type': transaction_type,
                'method': method,
                'amount': amount,
                'currency_code': currency_code.upper(),
                'credit_card': {
                    'type': card_type,
                    'cardholder_name': cardholder_name,
                    'card_number': card_number,
                    'exp_date': card_expiry,
                    'cvv': card_cvv,
                },
            }
        else:
            if transaction_id is None:
                raise ValueError, 'transaction_id cannot be None'
            if transaction_tag is None:
                raise ValueError, 'transaction_tag cannot be None'
            transaction_tag = str(transaction_tag)

            payload = {
                'merchant_ref': description,
                'transaction_tag': transaction_tag,
                'transaction_type': transaction_type,
                'method': method,
                'amount': amount,
                'currency_code': currency_code.upper(),
            }

        return {'payload': payload, 'transaction_id': transaction_id}

    def make_token_payload(self, ta_token=None, callback=None,
        token_type='FDToken', card_type=None, cardholder_name=None,
        card_number=None, exp_date=None, cvv=None, city=None,
        country=None, email=None, phone_type=None, phone_number=None,
        street=None, state=None, zip_code=None, js_security_key=None,
        ):
        """Make the token data dictionary for the get request.

        Payeezy Doc - https://developer.payeezy.com/payeezy-api/apis/get/securitytokens

        Parameters
        ----------
        ta_token : str, required
        callback : str, required
        token_type : str, required
        card_type : str, required
        cardholder_name : str, required
        card_number : str, required
        exp_date : str, required
        cvv : str, required
        city : str, required
        country : str, optional
        email : str, optional
        phone_type : str, optional
        phone_number : str, optional
        street : str, optional
        state : str, optional
        zip_code : str, optional
        js_security_key : str, required
        
        Returns
        -------
        dict
            Data payload for the token get request.
        
        Raises
        ------
        ValueError

        """
        allowed_cards = [
            'american express', 'visa', 'mastercard',
            'jcb', 'diners club', 'discover',
        ]
        if ta_token is None:
            raise ValueError('ta_token cannot be None.  Use 123 for sandbox environment.')
        if callback is None:
            callback = 'notProvided'
        if card_type is None:
            raise ValueError('card_type cannot be None. Allowed: {}'.format(allowed_cards))
        if cardholder_name is None:
            raise ValueError('cardholder_name cannot be None.')
        if js_security_key is None:
            raise ValueError('js_security_key cannot be None.')
        if card_number is None:
            raise ValueError('card_number cannot be None.')
        card_number = str(card_number)
        if exp_date is None:
            raise ValueError('exp_date cannot be None.  Use MMYY format')
        exp_date = str(exp_date)
        if cvv is None:
            raise ValueError('cvv cannot be None.')
        cvv = str(cvv)

        billing_address = {
            'phone': {}
        }

        if city is not None:
            billing_address['city'] = city
        if country is not None:
            billing_address['country'] = country
        if email is not None:
            billing_address['email'] = email
        if phone_type is not None:
            billing_address['phone']['type'] = phone_type
        if phone_number is not None:
            phone_number = str(phone_number)
            billing_address['phone']['number'] = phone_number
        if street is not None:
            billing_address['street'] = street
        if state is not None:
            billing_address['state_providence'] = state
        if zip_code is not None:
            zip_code = str(zip_code)
            billing_address['zip_postal_code'] = zip_code

        payload = {
            'type': token_type,
            'js_security_key': js_security_key,
            'ta_token': ta_token,
            'credit_card': {
                'type': card_type,
                'cardholder_name': cardholder_name,
                'card_number': card_number,
                'exp_date': exp_date,
                'cvv': cvv,
            },
            'billing_address': billing_address
        }

        return payload

    def make_primary_transaction(self, payload):
        auth = http_authorize.PayeezyHTTPAuthorize(
            self.api_key, self.api_secret, self.token,
            self.url, self.token_url,
        )
        return auth.makeCardBasedTransactionPostCall(payload)

    def make_secondary_transaction(self, payload, transaction_id):
        auth = http_authorize.PayeezyHTTPAuthorize(
            self.api_key, self.api_secret, self.token,
            self.url, self.token_url,
        )
        return auth.makeCaptureVoidRefundPostCall(payload, transaction_id)

    def authorize(self, amount=None, currency_code=None,
        card_type=None, cardholder_name=None, card_number=None,
        card_expiry=None, card_cvv=None, description=None,
        method='credit_card'
        ):
        """Authorize a credit card.
        
        Parameters
        ----------
        amount : float, optional
            Description
        currency_code : str, optional
            Description
        card_type : str, optional
            Description
        cardholder_name : str, optional
            Description
        card_number : str, optional
            Description
        card_expiry : str, optional
            Description
        card_cvv : str, optional
            Description
        description : str, optional
            Description
        method : str, optional
            Description
        
        Returns
        -------
        requests.Response
        
        """
        output = self.make_payload(
            amount=amount, currency_code=currency_code,
            card_type=card_type, cardholder_name=cardholder_name,
            card_number=card_number, card_expiry=card_expiry,
            card_cvv=card_cvv, description=description,
            method=method, transaction_type='authorize',
        )
        return self.make_primary_transaction(payload=output['payload'])

    def purchase(self, amount=None, currency_code=None, card_type=None,
        cardholder_name=None, card_number=None, card_expiry=None,
        card_cvv=None, description=None, method='credit_card'
        ):
        """Authorize + Capture in a single step.
        
        Parameters
        ----------
        amount : None, optional
            Description
        currency_code : None, optional
            Description
        card_type : None, optional
            Description
        cardholder_name : None, optional
            Description
        card_number : None, optional
            Description
        card_expiry : None, optional
            Description
        card_cvv : None, optional
            Description
        description : None, optional
            Description
        method : str, optional
            Description
        
        Returns
        -------
        requests.Response

        """
        output = self.make_payload(
            amount=amount, currency_code=currency_code,
            card_type=card_type, cardholder_name=cardholder_name,
            card_number=card_number, card_expiry=card_expiry,
            card_cvv=card_cvv, description=description,
            method=method, transaction_type='purchase',
        )
        return self.make_primary_transaction(payload=output['payload'])

    def capture(
        self, amount=None, currency_code=None, transaction_tag=None,
        transaction_id=None, description=None, method='credit_card',
        ):
        """
        """
        output = self.make_payload(
            amount=amount, currency_code=currency_code,
            transaction_tag=transaction_tag, transaction_id=transaction_id,
            description=description, transaction_type='capture',
            method=method,
        )
        r = self.make_secondary_transaction(
            payload=output['payload'], transaction_id=output['transaction_id']
        )
        return r

    def get_token(self):
        """
        """
        pass