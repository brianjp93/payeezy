"""Edited version of Payeezy's http_authorize file.
"""

import os, sys          # Standard system functions
import time             # Get Timestamp
import socket           # support functions for HTTPS connections - dependancy for HTTPAdapter
import ssl

import base64
from base64 import b64encode
import json
import hashlib      
import hmac
import requests

from requests.auth import HTTPBasicAuth
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.poolmanager import PoolManager

# TLSv1 protocol addition to HTTP adaptor for HTTPS calls
class MyAdapter(HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = PoolManager(num_pools=connections,
                                       maxsize=maxsize,
                                       block=block,
                                       ssl_version=ssl.PROTOCOL_TLSv1)

# HTTP authorization, headers generations and generic method to preform transactions and boarding operations.

class PayeezyHTTPAuthorize(object):

    # init function
    def __init__(self, apiKey, apiSecret, token, url, tokenurl):
        self.apikey = apiKey
        self.apisecret = apiSecret
        self.token = token
        self.url = url
        self.tokenurl = tokenurl
        # cryptographically strong random number
        self.nonce = str(int(os.urandom(16).encode('hex'),16))
        self.timestamp = str(int(round(time.time() * 1000)))
        self.timeout = 30 # max timeout is 30 sec

    # HMAC Generation
    def generateHMACAuthenticationHeader(self, payload):
        messageData = self.apikey+self.nonce+self.timestamp+self.token+payload
        hmacInHex = hmac.new(self.apisecret, msg=messageData, digestmod=hashlib.sha256).hexdigest()
        return b64encode(hmacInHex)

    # method to make calls for getToken 
    def getTokenPostCall(self, payload):
        response = requests.Session()
        response.mount('https://', MyAdapter())
        self.payload = json.dumps(payload)
        authorizationVal = self.generateHMACAuthenticationHeader(payload=self.payload)
        result = response.post(self.tokenURL, headers={'User-Agent':'Payeezy-Python','content-type': 'application/json','apikey':self.apikey,'token':self.token,'Authorization':'xxxxx'}, data=self.payload)
        return result
            
    #Generic method to make calls for primary transactions
    def makeCardBasedTransactionPostCall(self, payload):
        response = requests.Session()
        response.mount('https://', MyAdapter())
        self.payload = json.dumps(payload)
        authorizationVal = self.generateHMACAuthenticationHeader(payload=self.payload)
        result = response.post(self.url, headers={'User-Agent':'Payeezy-Python','content-type': 'application/json','apikey':self.apikey,'token':self.token,'nonce':self.nonce,'timestamp':self.timestamp,'Authorization':authorizationVal}, data=self.payload)
        return result


    #Generic method to make calls for secondary transactions
    def makeCaptureVoidRefundPostCall(self, payload, transactionID):
        response = requests.Session()
        response.mount('https://', MyAdapter())
        self.url =  self.url + '/' + transactionID
        self.payload = json.dumps(payload)
        authorizationVal = self.generateHMACAuthenticationHeader(payload=self.payload)
        result = response.post(self.url, headers={'User-Agent':'Payeezy-Python','content-type': 'application/json','apikey':self.apikey,'token':self.token,'nonce':self.nonce,'timestamp':self.timestamp,'Authorization':authorizationVal}, data=self.payload)
        return result

        