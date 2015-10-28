from time import clock
from time import sleep
from urllib.request import urlopen
import json


class VkApi:
    def __init__(self, name='VkApi', token=''):
        self.name = name

        self.token = token
        if token:
            self.enable_token = True
        else:
            self.enable_token = False

        self._url = 'https://api.vk.com/method/'
        self._version = '5.37'

        self.method_execute_query_count = 12

        self.sleep_time = 0.25
        self.except_time = 2
        self.except_count = 10
        self.__stamp_time = clock()

    def __set_time(self):
        self.__stamp_time = clock()

    def __get_diff_time(self):
        return clock() - self.__stamp_time

    def set_token(self, token):
        self.token = token
        self.enable_token = True

    def execute_query(self, method, options):
        query_url = '%s%s?%s' % (self._url, method, options)
        if self.enable_token:
            query_url += '&access_token=%s' % self.token

        query_url += '&v=%s' % self._version

        time_diff = self.__get_diff_time()
        if time_diff < self.sleep_time:
            sleep(self.sleep_time - time_diff)

        response = urlopen(query_url).read().decode()

        self.__set_time()

        return response

    def _use_execute(self, method_list, key_list=None):
        body = []
        execute_key = 0

        if not key_list:
            key_list = ['e_%d' % i for i in range(len(method_list))]

        for method_and_options in method_list:
            for method, options in method_and_options.items():
                body.append('"%s":API.%s(%s)' % (key_list[execute_key], method, str(json.dumps(options))))
            execute_key += 1

        body = ','.join(body)
        body = body.replace(' ', '')
        options = 'code=return{%s};' % body

        return self.execute_query(method='execute', options=options)

