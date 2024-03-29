from __future__ import print_function
import argparse
import importlib.machinery
import json
import os.path
import sys

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from os import makedirs
from os.path import expandvars, dirname

from retry import retry

import gfilter.dsl

SCOPES = [
            'https://www.googleapis.com/auth/gmail.settings.basic',
            'https://www.googleapis.com/auth/gmail.labels',
         ]

class Gmail:
    __service = None  # Client service stubs.
    __filters = None  # Cache of existing filter IDs.
    __labels = None   # Cache of existing labels. A dict of label -> id.


    # Retry in case we have exhausted quota.
    @retry(HttpError, tries=3, delay=2)
    def __execute(self, x):
        return x.execute()

    def login(self, credentials, token, access_token=None, developer_key=None):
        creds = None
        if access_token:
            creds = Credentials(access_token)
        elif os.path.exists(token):
            with open(token, 'r') as token:
                raw = json.load(token)
                creds = Credentials(
                        token=raw['token'],
                        refresh_token=raw['refresh_token'],
                        token_uri=raw['token_uri'],
                        client_id=raw['client_id'],
                        client_secret=raw['client_secret'])
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials, SCOPES)
                creds = flow.run_local_server()
            # Save the credentials for the next run
            with open(token, 'w') as token:
                raw = {'token': creds.token,
                       'refresh_token': creds.refresh_token,
                       'token_uri': creds.token_uri,
                       'client_id': creds.client_id,
                       'client_secret': creds.client_secret}
                json.dump(raw, token)

        self.__service = build('gmail', 'v1',
                               credentials=creds,
                               developerKey=developer_key)

    def get_filters(self):
        results = self.__execute(self.__service.users().settings().filters().list(userId='me'))
        self.__filters = results.get('filter', [])

    def delete_all_(self):
        self.get_filters()
        for f in self.__filters:
            self.__execute(self.__service.users().settings().filters().delete(
                    userId='me', id=f['id']))

    def get_labels(self):
        response = self.__execute(self.__service.users().labels().list(userId='me'))
        labels = response['labels']
        self.__labels = {
                # Magic labels:
                'STARRED': 'STARRED',
                'INBOX': 'INBOX',
                'SPAM': 'SPAM',
                'TRASH': 'TRASH',
                'UNREAD': 'UNREAD',
                'IMPORTANT': 'IMPORTANT',
                'CATEGORY_PERSONAL': 'CATEGORY_PERSONAL',
                'CATEGORY_SOCIAL': 'CATEGORY_SOCIAL',
                'CATEGORY_PROMOTIONS': 'CATEGORY_PROMOTIONS',
                'CATEGORY_UPDATES': 'CATEGORY_UPDATES',
                'CATEGORY_FORUMS': 'CATEGORY_FORUMS',
                }
        for label in labels:
            self.__labels[label['name']] = label['id']

    def create_label(self, label):  # TODO: label/message list visibility?
        result = self.__execute(self.__service.users().labels().create(userId='me',
                body={ 'name': label }))
        return result['id']

    def label_to_id(self, label):
        if label in self.__labels:
            return self.__labels[label]
        self.__labels[label] = self.create_label(label)
        return self.__labels[label]

    def upload(self, rules):  # TODO: type annotations


        for rule in rules:
            add_labels = [a.add_label for a in rule.actions
                          if a.add_label is not None]
            remove_labels = [a.remove_label for a in rule.actions
                             if a.remove_label is not None]

            # Apparently the Gmail API doesn't allow you to create a single
            # filter that applies two different user labels. I don't know why,
            # but anyway, we instead do one filter per add/remove label.
            body = {'criteria': {'query': rule.cond.query}}

            for label in add_labels:
                b = body.copy()
                b['action'] = {'addLabelIds': [self.label_to_id(label)]}
                self.__execute(self.__service.users().settings().filters().create(userId='me', body=b))
            for label in remove_labels:
                b = body.copy()
                b['action'] = {'removeLabelIds': [self.label_to_id(label)]}
                self.__execute(self.__service.users().settings().filters().create(userId='me', body=b))

def main():
    '''Uploads Gmail .
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument(
            'rules', help='Rules file')
    parser.add_argument(
            '-p', '--print', help='Print parsed rules', action='store_true')
    parser.add_argument(
            '-u', '--upload', help='Upload rules', action='store_true')
    parser.add_argument(
            '-n', '--nooverwrite', help='Don\'t overwrite existing rules',
            action='store_true')
    parser.add_argument(
            '--creds', help='Path to credentials JSON file',
            default='$HOME/.gfilter/credentials.json')
    parser.add_argument(
            '--token', help='Path to token JSON file',
            default='$HOME/.gfilter/token.json')
    # Use the below to bypass the installed-app flow.
    parser.add_argument(
            '--access_token', help='Access token.',
            default=None)
    parser.add_argument(
            '--developer_key', help='Developer key.',
            default=None)

    args = parser.parse_args()

    # Exec the input file.
    spec = importlib.util.spec_from_file_location(
            'imported_rules', args.rules)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # Print expected rules.
    if args.print:
        for rule in gfilter.dsl.RULES:
            print(rule)
    if args.upload:
        creds = expandvars(args.creds)
        token = expandvars(args.token)
        for f in [creds, token]:
            d = dirname(f)
            makedirs(d, exist_ok=True)

        gmail = Gmail()
        gmail.login(credentials=creds, token=token,
                    access_token=args.access_token,
                    developer_key=args.developer_key)
        gmail.get_labels()
        if not args.nooverwrite:
            gmail.delete_all_()
        gmail.upload(gfilter.dsl.RULES)

if __name__ == '__main__':
    main(sys.argv[1:])
