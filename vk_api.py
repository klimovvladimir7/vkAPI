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
        self.method_execute_query_count = 25
        self.sleep_time = 0.25
        self.except_time = 2
        self.except_count = 0
        self.except_max_count = 10
        self.__stamp_time = clock()

        self.enable_print = True

    def __set_time(self):
        self.__stamp_time = clock()

    def __get_diff_time(self):
        return clock() - self.__stamp_time

    def set_token(self, token):
        self.token = token
        self.enable_token = True

    def _execute_query(self, method, options):
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

    def __print_response_error(self, response):
        if self.enable_print:
            error_log = response.get('error')
            if error_log:
                error_code = error_log.get('error_code')
                error_msg = error_log.get('error_msg')
                print('error_code = %d (error_log = %s)' % (error_code, error_msg))
            else:
                print(response)

    def _get_response(self, method, options):
        while self.except_count <= self.except_max_count:
            response_text = self._execute_query(method, options)
            response_log = json.loads(response_text)
            response = response_log.get('response')
            if not response:
                self.except_count += 1
                sleep(self.except_time)
                self.__print_response_error(response_log)
            else:
                return response
        self.except_count = 0
        return None

    def _use_execute(self, method_list, key_list=None):
        body = []
        execute_key = 0
        if not key_list:
            key_list = ['_%d' % i for i in range(len(method_list))]

        for method_and_options in method_list:
            for method, options in method_and_options.items():
                body.append('"%s":API.%s(%s)' % (key_list[execute_key], method, str(json.dumps(options))))
            execute_key += 1

        body = ','.join(body)
        body = body.replace(' ', '')
        options = 'code=return{%s};' % body

        return self._get_response(method='execute', options=options)

    def _get_object_items(self, object_id, count, options, offset=0, additional_options=None):
        method = options.get('method')
        object_name = options.get('object_name')
        items_name = options.get('items_name')
        count_name = options.get('count_name')
        offset_name = options.get('offset_name')
        method_list = []

        for method_id in range(self.method_execute_query_count):
            method_options = {object_name: object_id, count_name: count, offset_name: offset}
            if additional_options:
                for options_key, options_value in additional_options.items():
                    method_options[options_key] = options_value
            method_list.append({method: method_options})
            offset += count

        response = self._use_execute(method_list)
        count_all = response.get('_0').get(count_name)

        items = []
        for method_id, execute_dict in response.items():
            items.extend(execute_dict.get(items_name))

        if count_all > offset:
            recursion_items_dict = self._get_object_items(
                object_id=object_id,
                count=count,
                options=options,
                offset=offset,
                additional_options=additional_options)

            if recursion_items_dict:
                recursion_items = recursion_items_dict.get(items_name)
                if recursion_items:
                    items.extend(recursion_items)

        return {count_name: count_all, items_name: items_name}

    def get_group_members(self, group_id):
        count = 1000
        options = {
            'method': 'groups.getMembers',
            'object_name': 'group_id',
            'items_name': 'items',
            'count_name': 'count',
            'offset_name': 'offset'
        }
        additional_options = {'sort': 'id_asc'}

        return self._get_object_items(
            object_id=group_id,
            count=count,
            options=options,
            additional_options=additional_options)
