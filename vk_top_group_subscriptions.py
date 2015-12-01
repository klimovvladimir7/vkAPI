from .data_processing import *
from .vk_api_threads import VkApiTreads
from .vk_api_downloader import VkApiDownloader
from os import path
from os import makedirs


def top_group_subscriptions(group_id, tokens_file_name, top_count=100, download_all_top_group=0):

    vk_api = VkApiTreads(tokens_file_name=tokens_file_name)
    member_ids = vk_api.run([group_id], 'get_group_members')[0].get(group_id).get('items')
    primordial_users_set = set(member_ids)

    with open(tokens_file_name, 'r') as file:
        tokens = [token for token in file]

    if not tokens:
        return

    dirs_list = ['data/users_groups_subscriptions/', 'data/group_members', 'data/tops', 'data/recovery_tops']
    for dir_name in dirs_list:
        try:
            makedirs(dir_name)
        except FileExistsError:
            pass

    users_groups_dir_name = 'data/users_groups_subscriptions'
    users_groups_file_name = 'users_groups_subscriptions_%d' % group_id

    groups_file_name = 'data/tops/groups_top_%d' % group_id
    pages_file_name = 'data/tops/pages_top_%d' % group_id

    group_members_output_file_name = 'group'
    group_members_output_dir = 'data/group_members'

    recovery_top_file_name = 'data/recovery_tops/recovery_top_%d' % group_id
    result_file = 'data/recovery_tops/top_info_%d' % group_id

    if not path.exists("%s/%s" % (users_groups_dir_name, users_groups_file_name)):
        vk_downloader = VkApiDownloader(tokens_file_name=tokens_file_name)
        vk_downloader.set_file_name(file_name=users_groups_file_name,
                                    dir_name=users_groups_dir_name,
                                    count=5000)
        vk_downloader.download(member_ids, method='get_users_groups')

    if (not path.exists(pages_file_name)) or (not path.exists(groups_file_name)):
        groups_top = get_groups_top('%s/%s' % (users_groups_dir_name, users_groups_file_name), top_count*20)

        pages_and_groups = sorted_by_pages_and_groups(groups_top=groups_top,
                                                      tokens_file_name=tokens_file_name,
                                                      pages_count=top_count,
                                                      groups_count=top_count)

        save_pages_and_groups(pages_and_groups=pages_and_groups,
                              pages_file_name=pages_file_name,
                              groups_file_name=groups_file_name)

    tokens_count = len(tokens)

    while tokens_count:
        try:
            download_groups_members(groups_file_name=groups_file_name,
                                    tokens_file_name=tokens_file_name,
                                    output_dir=group_members_output_dir,
                                    output_file_name=group_members_output_file_name,
                                    save_count=tokens_count)
            tokens_count = 0
        except MemoryError:
            print('download_groups_members: MemoryError')
            tokens_count -= 1
    tokens_count = len(tokens)

    while tokens_count:
        try:
            download_groups_members(groups_file_name=pages_file_name,
                                    tokens_file_name=tokens_file_name,
                                    output_dir=group_members_output_dir,
                                    output_file_name=group_members_output_file_name,
                                    save_count=tokens_count)
            tokens_count = 0
        except MemoryError:
            print('download_groups_members: MemoryError')
            tokens_count -= 1

    if not path.exists(recovery_top_file_name):
        recovery_groups_top = get_recovery_groups_top(groups_file_name=groups_file_name,
                                                      dir_name=group_members_output_dir,
                                                      template_name=group_members_output_file_name,
                                                      primordial_users_set=primordial_users_set)

        recovery_pages_top = get_recovery_groups_top(groups_file_name=pages_file_name,
                                                     dir_name=group_members_output_dir,
                                                     template_name=group_members_output_file_name,
                                                     primordial_users_set=primordial_users_set)

        save_recovery_top(recovery_groups_top, recovery_pages_top, top_count, recovery_top_file_name)

    recovery_top = read_top(top_file_name=recovery_top_file_name)

    api_threads = VkApiTreads(tokens_file_name=tokens_file_name)
    object_ids = [group_id for group_id in recovery_top.keys()]
    response_list = api_threads.run(object_ids=object_ids, method='get_groups_info')

    response_dict = {}
    for response in response_list:
        for group_info in response:
                group_id = group_info.get('id')
                screen_name = group_info.get('screen_name')
                members_count = group_info.get('members_count')
                name = group_info.get('name').replace('|', ' ')
                top_value = recovery_top.get(group_id).get('top_value')
                response_dict[group_id] = '%d - %s (%s : %d)' % (top_value, name, screen_name, members_count)

    top_dict = {group_id: group_info.get('top_value') for (group_id, group_info) in recovery_top.items()}
    top_sort = (group_id for group_id in sorted(top_dict, key=top_dict.get, reverse=True))

    with open(result_file, 'w', encoding="utf-8") as file:
        for group_id in top_sort:
            file.write('%s\n' % response_dict.get(group_id))


