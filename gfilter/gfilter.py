from __future__ import print_function
import argparse
import importlib.machinery
import json
import os.path
import sys

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

import gfilter.dsl

SCOPES = [
            'https://www.googleapis.com/auth/gmail.settings.basic',
            'https://www.googleapis.com/auth/gmail.labels',
         ]

class Gmail:
    __service = None  # Client service stubs.
    __filters = None  # Cache of existing filter IDs.
    __labels = None   # Cache of existing labels. A dict of label -> id.

    def login(self):
        creds = None
        if os.path.exists('token.json'):
            with open('token.json', 'r') as token:
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
                    'credentials.json', SCOPES)
                creds = flow.run_local_server()
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                raw = {'token': creds.token,
                       'refresh_token': creds.refresh_token,
                       'token_uri': creds.token_uri,
                       'client_id': creds.client_id,
                       'client_secret': creds.client_secret}
                json.dump(raw, token)

        self.__service = build('gmail', 'v1', credentials=creds)

    def get_filters(self):
        results = self.__service.users().settings().filters().list(userId='me').execute()
        self.__filters = results.get('filter', [])

    def delete_all_(self):
        self.get_filters()
        for f in self.__filters:
            self.__service.users().settings().filters().delete(
                    userId='me', id=f['id']).execute()

    def get_labels(self):
        response = self.__service.users().labels().list(userId='me').execute()
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
        result = self.__service.users().labels().create(userId='me',
                body={ 'name': label }).execute()
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

            self.__service.users().settings().filters().create(userId='me', body={
                'criteria': {
                    'query': rule.cond.query,
                },
                'action': {
                    'addLabelIds': [self.label_to_id(label) for label in add_labels],
                    'removeLabelIds': [self.label_to_id(label) for label in remove_labels],
                }
            }).execute()


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
    args = parser.parse_args()

    # Exec the input file.
    spec = importlib.util.spec_from_file_location(
            'imported_rules', args.rules)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # Print expected rules.
    print('Parsed %d rules.' % len(gfilter.dsl.RULES))
    if args.print:
        for rule in gfilter.dsl.RULES:
            print(rule)
    if args.upload:
        gmail = Gmail()
        gmail.login()
        gmail.get_labels()
        if not args.nooverwrite:
            gmail.delete_all_()
        gmail.upload(gfilter.dsl.RULES)

if __name__ == '__main__':
    main(sys.argv[1:])
