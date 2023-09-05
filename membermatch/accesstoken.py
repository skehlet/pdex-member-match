#! /usr/bin/env python3
# fhir_tooling
# : AccessToken.py
# Create  Class for AccessToken

__author__ = "@ekivemark"
# 2023-08-23 5:46 PM

import logging
import requests
import time

from urllib.parse import urlencode

logging.basicConfig(level=logging.INFO,
                    filename='membermatch_%s.log' % 'info',
                    filemode='w',
                    format='%(message)s - %(filename)s - %(asctime)-15s')


class AccessToken:
    """
    Get an Access Token
    """
    def __init__(self, client_id, client_secret, target_paas, tenant, auth_url):
        self.expiry = int(time.time())
        self.access_token = ""
        self.client_id = client_id
        self.client_secret = client_secret
        self.target_paas = target_paas
        self.tenant = tenant
        if auth_url:
            self.AUTH_URL = auth_url
        else:
            self.AUTH_URL = "https://login.microsoftonline.com/%s/oauth2/token" % self.tenant

    def __repr__(self):
        return self.access_token

    def get_token(self):
        """ Get access token."""
        time_now = int(time.time())
        # print(f"{time_now} | {self.expiry} ")
        if time_now < int(self.expiry):
            # print("We didn't have to get a new token")
            return self.access_token
        # token has expired so get a new one
        self.HEADERS = {"Accept": "application/json",
                        "Content-Type": "application/x-www-form-urlencoded"}

        self.form = {"grant_type": "client_credentials",
                     "resource": self.target_paas,
                     "client_id": self.client_id,
                     "client_secret": self.client_secret}
        self.data = urlencode(self.form)
        try:
            self.response = requests.post(self.AUTH_URL, data=self.data, headers=self.HEADERS)
        except ValueError:
            logging.info(f"Value Error retrieving access_token")
        if self.response.status_code != 200:
            logging.info(f"{self.response.status_code}:Problem with call to {self.AUTH_URL}")
            logging.info(f"AUTH_URL Response:{self.response.content}")
        else:
            if "access_token" in self.response.json():
                logging.info(f"Received access token from {self.AUTH_URL}")
                self.access_token = self.response.json()['access_token']
                self.expiry = self.response.json()['expires_on']
        return self.access_token
