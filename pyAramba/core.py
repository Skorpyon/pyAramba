# -*- coding: utf-8 -*-

import json
import requests

from datetime import datetime

from .exceptions import ArambaAPIError, ArambaEngineError, ArambaValueError


METHODS = ['get', 'post', 'put', 'patch', 'delete', 'options']
ERROR_CODES = [400, 401, 402, 403, 404, 409, 500]

# Aramba API URLs
API_URL = 'https://api.aramba.ru'
SMS_SENDER_IDS = 'smsSenderIds'

BALANCE = 'balance'

SINGLE_SMS = 'singleSms'
SMS_SENDINGS = 'smsSendings'

CONTACT_GROUPS = 'contactGroups'
GROUP_CONTACTS = 'contacts'


class SmsStatus(object):
    NEW = 'new'
    ENROUTE = 'enroute'
    DELIVERED = 'delivered'
    UNDELIVERABLE = 'undeliverable'
    ERROR = 'error'

    CHOICES = (
        (NEW, 'Новая SMS'),
        (ENROUTE, 'Отправлено'),
        (DELIVERED, 'Доставлено'),
        (UNDELIVERABLE, 'Невозможно доставить'),
        (ERROR, 'Ошибка при отправке'),
    )


class Sms(object):

    status = SmsStatus.NEW
    send_datetime = None
    use_recipient_timezone = False

    status_code = None
    cost = None
    planned_utc_datetime = None
    delivery_utc_datetime = None

    def __init__(self, sender_engine, number: str, content:  str, sender_id=None,
                 send_datetime=None, use_recipient_timezone=None):
        self.sender_engine = sender_engine

        # Proceed number
        number = number.rstrip('+').rstrip('00').strip('-').strip()
        try:
            self.number = int(number)
        except ValueError:
            raise ArambaValueError('Phone number should be in "+<country_code> XXX XXX XX XX" format.')
        else:
            self.number = str(self.number)

        # Set sender id
        if sender_id is not None:
            self.sender_id = sender_id
        else:
            self.sender_id = self.sender_engine.sender_id

        # Proceed send datetime
        if send_datetime is not None:
            if isinstance(send_datetime, datetime):
                self.send_datetime = send_datetime
            else:
                raise ArambaValueError('Send_datetime should be a datetime instance.')
        if use_recipient_timezone is not None:
            if isinstance(use_recipient_timezone, bool):
                self.use_recipient_timezone = use_recipient_timezone
            else:
                raise ArambaValueError('Use_recipient_timezone should be a boolean.')

        self.content = content
        self.id = None

    @property
    def result(self):
        return {
            'status_code': self.status_code,
            'id': self.id,
            'status': self.status,
            'cost': self.cost,
            'number': self.number,
            'content': self.content,
            'planned_utc_datetime': self.planned_utc_datetime,
            'delivery_utc_datetime': self.delivery_utc_datetime
        }

    def send(self):
        if self.status in [SmsStatus.NEW, SmsStatus.ERROR]:
            try:
                result = self.sender_engine._send_sms(self)
            except ArambaAPIError as e:
                self.status = 'error'
                self.status_code = e.status_code

            else:
                self.status_code = result.status_code

                json_result = result.json()
                self.status = json_result['status'].lower()
                self.id = json_result['id']
                self.cost = json_result['cost']
                self.number = json_result['phoneNumber']
                self.content = json_result['text']
                self.planned_utc_datetime = json_result['plannedUtcDateTime']
                self.delivery_utc_datetime = json_result['deliveryUtcDateTime']

        return self


class MultipleSMS(object):
    results = list()
    status = SmsStatus.NEW
    send_datetime = None
    use_recipient_timezone = False

    status_code = None
    cost = None
    planned_utc_datetime = None
    delivery_utc_datetime = None

    def __init__(self, sender_engine, numbers: list, content:  str, sender_id=None,
                 send_datetime=None, use_recipient_timezone=None):
        self.sender_engine = sender_engine

        # Proceed number
        numbers_list = list()
        for number in numbers:
            number = number.rstrip('+').rstrip('00').strip('-').strip()
            try:
                self.number = int(number)
            except ValueError:
                raise ArambaValueError('Phone number should be in "+<country_code> XXX XXX XX XX" format.')
            else:
                numbers_list.append(number)
        self.numbers = numbers_list

        # Set sender id
        if sender_id is not None:
            self.sender_id = sender_id
        else:
            self.sender_id = self.sender_engine.sender_id

        # Proceed send datetime
        if send_datetime is not None:
            if isinstance(send_datetime, datetime):
                self.send_datetime = send_datetime
            else:
                raise ArambaValueError('Send_datetime should be a datetime instance.')
        if use_recipient_timezone is not None:
            if isinstance(use_recipient_timezone, bool):
                self.use_recipient_timezone = use_recipient_timezone
            else:
                raise ArambaValueError('Use_recipient_timezone should be a boolean.')

        self.content = content
        self.id = None

    @property
    def result(self):
        return self.results

    def send(self):
        if self.status in [SmsStatus.NEW, SmsStatus.ERROR]:
            try:
                result = self.sender_engine._send_bulk_sms(self)
            except ArambaAPIError as e:
                self.status = 'error'
                self.status_code = e.status_code

            else:
                self.status_code = result.status_code
                results = list()
                json_result = result.json()
                for key, value in json_result.items():
                    results.append({
                        'status': value['status'].lower(),
                        'id': value['id'],
                        'cost': value['cost'],
                        'number': value['phoneNumber'],
                        'content': value['text'],
                        'planned_utc_datetime': value['plannedUtcDateTime'],
                        'delivery_utc_datetime': value['deliveryUtcDateTime']
                    })
                self.results = results

        return self


class SmsSender(object):
    # SMS Queue
    _queue = list()

    # Sender IDs
    default_sender_id = None
    _available_sender_ids = None
    _sms_sender_offset = 0
    _sms_sender_limit = 50

    def __init__(self, api_key: str, sender_id=None):
        self.api_key = api_key

        # Set Sender Id
        if sender_id is None and self.default_sender_id is None:
            raise ArambaEngineError('You should pass Sender ID or "set default_sender_id".')
        elif sender_id is not None:
            self.sender_id = sender_id
        else:
            self.sender_id = self.default_sender_id

        self._authorization_header = 'ApiKey %s' % self.api_key

    @staticmethod
    def _build_url(url):
        url_list = list(API_URL)
        if isinstance(url, str):
            url_list.append(url)
        elif isinstance(url, (list, set)):
            for u in url:
                url_list.append(u)
        return '/'.join(url_list)

    @staticmethod
    def _raise_aramba_api_error(status_code, message):
        raise ArambaAPIError('%s Status code: %s.' % (message, status_code),  status_code)

    @property
    def queue(self):
        return self._queue

    def _make_request(self, method, url, data=None, headers=None):
        # Check that method exists
        if method not in METHODS:
            raise ArambaValueError('Unknown method "%s". Available methods: %s.' % (method, METHODS))

        # Set authorization header
        if headers is None:
            headers = dict()
        headers.update({'Authorization': self._authorization_header})
        headers.update({'Accept': 'application/json'})
        headers.update({'Content-Type': 'application/json'})

        # Set data
        if data is None:
            data = dict()

        # Make API request
        s = requests.Session()
        req = requests.Request(method=method, url=url, data=data, headers=headers)
        prepped = req.prepare()
        response = s.send(prepped)
        status_code = response.status_code
        if status_code in ERROR_CODES:
            if status_code == 400:
                self._raise_aramba_api_error(status_code, 'Bad request.')
            elif status_code == 401:
                self._raise_aramba_api_error(status_code, 'Not authorized.')
            elif status_code == 402:
                self._raise_aramba_api_error(status_code, 'Payment required.')
            elif status_code == 403:
                self._raise_aramba_api_error(status_code, 'This action is not permitted for given API key.')
            elif status_code == 404:
                self._raise_aramba_api_error(status_code, 'Not found.')
            elif status_code == 409:
                self._raise_aramba_api_error(status_code, 'Conflict.')
            elif status_code == 500:
                self._raise_aramba_api_error(status_code, 'Internal server error.')

        return response

    def available_sender_ids(self, offset=None, limit=None):
        if self._available_sender_ids is None\
                or self._sms_sender_offset != offset\
                or self._sms_sender_limit != limit:

            # Validate limit attr
            if limit is not None and isinstance(limit, int):
                if 0 < limit <= 500:
                    self._sms_sender_limit = limit
                else:
                    raise ArambaValueError('Limit should be integer between 0 and 500.')

            # Validate offset attr
            if offset is not None and isinstance(offset, int):
                self._sms_sender_limit = limit

            data = {
                'Offset': self._sms_sender_offset,
                'Limit': self._sms_sender_limit
            }
            url = self._build_url(SMS_SENDER_IDS)
            response = self._make_request(method='get', url=url, data=data)
            json_response = response.json()
            self._available_sender_ids = json_response['items']

        return self._available_sender_ids

    def ask_balance(self):
        url = self._build_url(BALANCE)
        return self._make_request('get', url)

    # Contact groups
    def create_group(self, name):
        url = self._build_url(CONTACT_GROUPS)
        data = {'name': name}
        return self._make_request('post', url, data)

    def retrieve_group(self, group_id):
        url = self._build_url([CONTACT_GROUPS, group_id])
        return self._make_request('get', url)

    def update_group(self, group_id, name):
        url = self._build_url([CONTACT_GROUPS, group_id])
        data = {'name': name}
        return self._make_request('put', url, data)

    def delete_group(self, group_id):
        url = self._build_url([CONTACT_GROUPS, group_id])
        return self._make_request('delete', url)

    # Contacts
    def create_contact(self, group_id, data):
        url = self._build_url([CONTACT_GROUPS, group_id, GROUP_CONTACTS])
        return self._make_request('post', url, data)

    def retrieve_contact(self, group_id, contact_id):
        url = self._build_url(
            [CONTACT_GROUPS, group_id, GROUP_CONTACTS, contact_id])
        return self._make_request('get', url)

    def update_contact(self, group_id, contact_id, data):
        url = self._build_url(
            [CONTACT_GROUPS, group_id, GROUP_CONTACTS, contact_id])
        return self._make_request('put', url, data)

    def delete_contact(self, group_id, contact_id):
        url = self._build_url(
            [CONTACT_GROUPS, group_id, GROUP_CONTACTS, contact_id])
        return self._make_request('delete', url)

    # Bulk SMS sendings
    def _send_bulk_sms(self, sms):
        if not isinstance(sms, MultipleSMS):
            raise ArambaValueError(
                'Value for send_sms should be MultipleSMS instance.')
        data = {
            'senderId': sms.sender_id,
            'SendDateTime': sms.send_datetime,
            'UseRecipientTimeZone': sms.use_recipient_timezone,
            'PhoneNumbers': sms.numbers,
            'Text': sms.content
        }
        url = self._build_url([SINGLE_SMS, 'multiple'])
        data = json.dumps(data)
        return self._make_request(method='post', url=url, data=data)

    def _send_sms(self, sms):
        if not isinstance(sms, Sms):
            raise ArambaValueError('Value for send_sms should be Sms instance.')
        data = {
            'senderId': sms.sender_id,
            'SendDateTime': sms.send_datetime,
            'UseRecipientTimeZone': sms.use_recipient_timezone,
            'PhoneNumber': str(sms.number),
            'Text': sms.content
        }
        url = self._build_url(SINGLE_SMS)
        data = json.dumps(data)
        return self._make_request(method='post', url=url, data=data)

    def send(self):
        for sms in self._queue:
            sms.send()

    def append_new_sms(self, number: str, content: str, sender_id=None, send_datetime=None):
        new_sms = Sms(self, number, content, sender_id, send_datetime)
        self._queue.append(new_sms)