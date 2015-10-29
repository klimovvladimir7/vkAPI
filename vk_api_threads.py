from threading import Thread
from vk_api import VkApi


class VkApiTreads:

    def __init__(self, tokens_file_name=''):
        self.tokens = []
        self._api_list = []
        self._threads = []
        if tokens_file_name:
            self.read_tokens(tokens_file_name)

    def _init_api_list(self):
        for i in range(len(self.tokens)):
            if i >= len(self._api_list):
                self._api_list.append(VkApi(name=('job_%d' % i), token=self.tokens[i]))
                self._threads.append(None)

    def set_tokens(self, tokens):
        self.tokens.extend(tokens)
        self._init_api_list()

    def set_token(self, token):
        self.tokens.append(token)
        self._init_api_list()

    def read_tokens(self, file_name):
        with open(file_name, 'r') as file:
            self.tokens.extend([token for token in file.read().split('\n') if len(token)])
        self._init_api_list()

    def _get_thread_response(self, object_ids, api_class_id, method, threads_responses):
        if object_ids:
            threads_responses.append(self._api_list[api_class_id].run_method(object_ids, method))

    def _split_object_ids(self, object_ids):
        parts_count = len(self.tokens)
        interval_len = int(len(object_ids)/parts_count)
        parts = []
        offset = 0
        for interval_id in range(parts_count):
            part = []
            for object_iter in range(interval_len):
                part.append(object_ids[offset+object_iter])
            offset += interval_len
            parts.append(part)
        for object_iter in range(offset, len(object_ids)):
            parts[object_iter % parts_count].append(object_ids[object_iter])
        return parts

    def run(self, object_ids, method):
        object_ids_parts = self._split_object_ids(object_ids)
        threads_count = len(self.tokens)
        threads_responses = []
        for thread_id in range(threads_count):
            self._threads[thread_id] = Thread(target=self._get_thread_response,
                                              args=(object_ids_parts[thread_id],
                                                    thread_id,
                                                    method,
                                                    threads_responses))
        for thread in self._threads:
            thread.start()
        for thread in self._threads:
            thread.join()
        return threads_responses
