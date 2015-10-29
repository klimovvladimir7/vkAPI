from os import makedirs
from vk_api_threads import VkApiTreads


class VkApiDownloader:

    def __init__(self, tokens_file_name='', count=1000, dir_name='data', file_name='download'):
        self.vk_api_threads = VkApiTreads(tokens_file_name=tokens_file_name)
        self.dir_name = dir_name
        self.file_name = file_name
        self.file_name_info = '_' + self.file_name
        self.count = count
        self._hash = set()
        self._dir_init()
        self._hash_init()

    def _dir_init(self):
        try:
            makedirs(self.dir_name)
        except OSError:
            pass

    def _hash_init(self):
        try:
            with open('%s/%s' % (self.dir_name, self.file_name_info), 'r') as file:
                self._hash = set([int(row) for row in file if row])
        except OSError:
            pass

    def set_file_name(self, file_name, dir_name=None):
        self.file_name = file_name
        if dir_name:
            self.dir_name = dir_name
        self._dir_init()
        self._hash_init()

    def _split_object_ids_part(self, object_ids):
        parts = []
        part = []
        object_ids_iter = 1
        for object_id in object_ids:
            if object_id not in self._hash:
                if object_ids_iter % self.count == 0:
                    parts.append(part)
                    part = []
                part.append(object_id)
                object_ids_iter += 1
        parts.append(part)
        return parts

    def _write_response_list(self, response_list, method):
        for response in response_list:

            if method == 'get_users_groups':
                for object_id, object_info in response.items():
                    if object_info:
                        items = object_info.get('items')
                        if items:
                            row = '%s:%s\n' % (object_id,
                                               ','.join([str(item) for item in items]))
                            with open('%s/%s' % (self.dir_name, self.file_name), 'a') as file:
                                file.write(row)
                            with open('%s/%s' % (self.dir_name, self.file_name_info), 'a') as file:
                                file.write(str(object_id) + '\n')

            elif method == 'get_group_members':
                for object_id, object_info in response.items():
                    if object_info:
                        items = object_info.get('items')
                        if items:
                            rows = '\n'.join([str(item) for item in items])
                            with open('%s/%s_%s' % (self.dir_name, self.file_name, str(object_id)), 'a') as file:
                                file.write(rows)
                            with open('%s/%s' % (self.dir_name, self.file_name_info), 'a') as file:
                                file.write(str(object_id) + '\n')

    def download(self, object_ids, method):
        object_ids_parts = self._split_object_ids_part(object_ids)
        for object_ids_part in object_ids_parts:
            response_list = self.vk_api_threads.run(object_ids=object_ids_part, method=method)
            self._write_response_list(response_list, method)
