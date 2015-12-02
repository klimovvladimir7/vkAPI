from .vk_api_threads import VkApiTreads
from .vk_api_downloader import VkApiDownloader


def get_groups_top(file_name, count):
    groups_top = {}
    with open(file_name, 'r') as file:
        for row in file:
            if row:
                row_data = row.split(':')
                if row_data:
                    group_ids = [int(group_id) for group_id in row_data[1].split(',') if group_id]
                    for group_id in group_ids:
                        groups_top[group_id] = int(groups_top.get(group_id) or 0) + 1

    groups_top_sort = ((group_id, groups_top[group_id]) for group_id in sorted(groups_top,
                                                                               key=groups_top.get,
                                                                               reverse=True))
    result_groups_top = {}
    for group_id, value in groups_top_sort:
        result_groups_top[group_id] = value
        if len(result_groups_top) > count:
            return result_groups_top
    return result_groups_top


def sorted_by_pages_and_groups(groups_top, tokens_file_name, pages_count, groups_count):
    api_threads = VkApiTreads(tokens_file_name=tokens_file_name)
    object_ids = [group_id for group_id in groups_top.keys()]
    response_list = api_threads.run(object_ids=object_ids, method='get_groups_info')
    pages_and_groups_info = {'group': {}, 'page': {}}
    pages_and_groups_top = {'group': {}, 'page': {}}

    for response in response_list:
        for group_info in response:
            group_id = group_info.get('id')
            group_type = group_info.get('type')
            if group_type == 'group' or group_type == 'page':
                pages_and_groups_info.get(group_type)[group_id] = {"screen_name": group_info.get('screen_name'),
                                                                   'is_closed': group_info.get('is_closed'),
                                                                   'members_count': group_info.get('members_count'),
                                                                   'top_value': groups_top.get(group_id)}
    pages_and_groups_max_count = {'group': groups_count, 'page': pages_count}
    for category_name, category in pages_and_groups_info.items():
        top = {item_id: category.get(item_id).get('top_value') for (item_id, item) in category.items()}
        for item_id in (item_id for item_id in sorted(top, key=top.get, reverse=True)):
            pages_and_groups_top.get(category_name)[item_id] = category.get(item_id)
            if len(pages_and_groups_top.get(category_name)) >= pages_and_groups_max_count.get(category_name):
                break
    return pages_and_groups_top


def save_pages_and_groups(pages_and_groups, pages_file_name, groups_file_name):
    file_names = {'page': pages_file_name, 'group': groups_file_name}
    for category_name, category in pages_and_groups.items():
        top = {item_id: item.get('top_value') for (item_id, item) in category.items()}
        with open(file_names.get(category_name), 'w') as output_file:
            for item_id in (item_id for item_id in sorted(top, key=top.get, reverse=True)):
                member_count = category.get(item_id).get('members_count')
                top_value = category.get(item_id).get('top_value')
                if not category.get(item_id).get('is_closed') and member_count:
                    output_file.write('%s:%s:%s\n' % (item_id, str(member_count), top_value))


def download_groups_members(groups_file_name, output_dir, tokens_file_name, output_file_name, save_count):
    print('download_groups_members')
    groups = read_top(groups_file_name)
    groups_ids = [group_id for group_id in sorted(groups, key=groups.get('members_count'), reverse=False)]
    if groups_ids:
        downloader = VkApiDownloader(tokens_file_name=tokens_file_name)
        downloader.set_file_name(file_name=output_file_name, dir_name=output_dir, count=save_count)
        downloader.download(groups_ids, method='get_group_members')


def get_recovery_groups_top(groups_file_name, dir_name, template_name, primordial_users_set):
    with open(groups_file_name, 'r') as file:
        group_list = [int(row.strip('\n').split(':')[0]) for row in file if row]

    recovery_top = {}
    for group_id in group_list:
        try:
            with open('%s/%s_%d' % (dir_name, template_name, group_id), 'r') as file:
                members = set(int(row.strip('\n')) for row in file if row)
            top_value = len(members & primordial_users_set)
            recovery_top[group_id] = {'top_value': top_value, 'members_count': len(members)}
			members.clear()
            print('get_recovery_groups_top: group_id = %d top_value = %d' % (group_id, top_value))
        except FileNotFoundError:
            print('get_recovery_groups_top: file %s/%s_%d not found)' % (dir_name, template_name, group_id))
    return recovery_top


def read_top(top_file_name):
    page_top = {}
    with open(top_file_name, 'r') as file:
        for row in file:
            if row:
                row_data = [int(i) for i in row.strip('\n').split(':')]
                page_id = row_data[0]
                members_count = row_data[1]
                top_value = row_data[2]
                page_top[page_id] = {'members_count': members_count, 'top_value': top_value}
    return page_top


def save_recovery_top(recovery_groups_top, recovery_pages_top, count, recovery_top_file_name):
    union_top = recovery_groups_top.copy()
    for page_id, page_info in recovery_pages_top.items():
        union_top[page_id] = page_info
    top = {group_id: group_info.get('top_value') for (group_id, group_info) in union_top.items()}
    result_top = {}
    with open(recovery_top_file_name, 'w') as file:
        for group_id, top_value in ((group_id, top[group_id]) for group_id in sorted(top, key=top.get, reverse=True)):
            members_count = union_top.get(group_id).get('members_count')
            file.write('%d:%s:%d\n' % (group_id, str(members_count), top_value))
            result_top[group_id] = top_value
            if len(result_top) > count:
                break
    return result_top
