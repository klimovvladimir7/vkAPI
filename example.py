from vk_api_downloader import VkApiDownloader
from vk_api_threads import VkApiTreads

x = VkApiDownloader(tokens_file_name='tokens.txt')

# download users_groups
ids = [i for i in range(1, 2000)]
x.set_file_name(file_name='users_groups', dir_name='users_group_data', count=1000)
x.download(ids, method='get_users_groups')

# download group_members
ids = [i for i in range(1, 20)]
x.set_file_name(file_name='group', dir_name='group_members_data', count=5)
x.download(ids, method='get_group_members')

# print groups info
x = VkApiTreads(tokens_file_name='tokens.txt')
object_ids = [i for i in range(1, 100)]
response_list = x.run(object_ids=object_ids, method='get_groups_info')
for response in response_list:
    for i in response:
            print(i.get('id'), i.get('screen_name'), i.get('type'), i.get('is_closed'), i.get('members_count'))
