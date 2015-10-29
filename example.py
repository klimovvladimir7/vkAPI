from vk_api_downloader import VkApiDownloader

x = VkApiDownloader(tokens_file_name='tokens.txt')

ids = [i for i in range(1, 2000)]
x.set_file_name(file_name='users_groups', dir_name='users_group_data', count=1000)
x.download(ids, method='get_users_groups')

ids = [i for i in range(1, 20)]
x.set_file_name(file_name='group', dir_name='group_members_data', count=5)
x.download(ids, method='get_group_members')
