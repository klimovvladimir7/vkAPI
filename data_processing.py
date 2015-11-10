from vk_api_threads import VkApiTreads
from vk_api_downloader import VkApiDownloader


def get_groups_top(file_name, count, count_print=0):
    groups_top = {}
    i = 1
    with open(file_name, 'r') as file:
        for row in file:
            if row:
                row_data = row.split(':')
                if len(row_data) > 1:
                    group_ids = [int(group_id) for group_id in row_data[1].split(',') if group_id]
                    for group_id in group_ids:
                        groups_top[group_id] = int(groups_top.get(group_id) or 0) + 1
            if count_print:
                i += 1
                if not i % count_print:
                    print('get_groups_top: offset = %d' % i)

    groups_top_sort = ((group_id, groups_top[group_id]) for group_id in sorted(groups_top,
                                                                               key=groups_top.get,
                                                                               reverse=True))
    i = 1
    result_groups_top = {}
    for group_id, value in groups_top_sort:
        result_groups_top[group_id] = value
        i += 1
        if i > count:
            break
    return result_groups_top


def sorted_by_pages_and_groups(groups_top, tokens_file_name, pages_count, groups_count):
    api_threads = VkApiTreads(tokens_file_name=tokens_file_name)
    object_ids = [group_id for group_id in groups_top.keys()]
    response_list = api_threads.run(object_ids=object_ids, method='get_groups_info')
    groups = {}
    pages = {}

    for response in response_list:
        for group_info in response:
            group_id = group_info.get('id')
            screen_name = group_info.get('screen_name')
            group_type = group_info.get('type')
            is_closed = group_info.get('is_closed')
            members_count = group_info.get('members_count')
            top_value = groups_top[group_id]
            if group_type == 'page':
                pages[group_id] = {"screen_name": screen_name,
                                   'is_closed': is_closed,
                                   'members_count': members_count,
                                   'top_value': top_value}
            elif group_type == 'group':
                groups[group_id] = {"screen_name": screen_name,
                                    'is_closed': is_closed,
                                    'members_count': members_count,
                                    'top_value': top_value}
    pages_top = {page_id: page_info.get('top_value') for (page_id, page_info) in pages.items()}
    pages_sort = (page_id for page_id in sorted(pages_top, key=pages_top.get, reverse=True))
    pages_top = {}
    page_iter = 0

    for page_id in pages_sort:
        pages_top[page_id] = pages.get(page_id)
        page_iter += 1
        if page_iter >= pages_count:
            break

    groups_top = {group_id: group_info.get('top_value') for (group_id, group_info) in groups.items()}
    groups_sort = (group_id for group_id in sorted(groups_top, key=groups_top.get, reverse=True))
    groups_top = {}
    group_iter = 0

    for group_id in groups_sort:
        groups_top[group_id] = groups.get(group_id)
        group_iter += 1
        if group_iter >= groups_count:
            break
    return {'pages': pages_top, 'groups': groups_top}


def save_pages_and_groups(pages_and_groups, pages_file_name, groups_file_name):
    pages = pages_and_groups.get('pages')
    pages_top = {page_id: page_info.get('top_value') for (page_id, page_info) in pages.items()}
    pages_sort = (page_id for page_id in sorted(pages_top, key=pages_top.get, reverse=True))

    with open(pages_file_name, 'w') as file:
        for page_id in pages_sort:
            page_info = pages.get(page_id)
            is_closed = page_info.get('is_closed')
            member_count = page_info.get('members_count')
            top_value = page_info.get('top_value')
            if not is_closed and member_count:
                file.write('%s:%s:%s\n' % (str(page_id), str(member_count), str(top_value)))

    groups = pages_and_groups.get('groups')
    groups_top = {group_id: group_info.get('top_value') for (group_id, group_info) in groups.items()}
    groups_sort = (group_id for group_id in sorted(groups_top, key=groups_top.get, reverse=True))

    with open(groups_file_name, 'w') as file:
        for group_id in groups_sort:
            group_info = groups.get(group_id)
            is_closed = group_info.get('is_closed')
            member_count = group_info.get('members_count')
            top_value = group_info.get('top_value')
            if not is_closed and member_count:
                file.write('%s:%s:%s\n' % (str(group_id), str(member_count), str(top_value)))


def download_groups_members(groups_file_name, output_dir, tokens_file_name, output_file_name):
    groups = {}
    with open(groups_file_name, 'r') as file:
        for row in file:
            if row:
                row_data = row.strip('\n').split(':')
                group_id = int(row_data[0])
                members_count = int(row_data[1])
                if group_id and members_count:
                    groups[group_id] = members_count

    groups_ids = [group_id for group_id in sorted(groups, key=groups.get, reverse=False)]

    if groups_ids:
        downloader = VkApiDownloader(tokens_file_name=tokens_file_name)
        downloader.set_file_name(file_name=output_file_name, dir_name=output_dir, count=10)
        downloader.download(groups_ids, method='get_group_members')


def get_recovery_groups_top(groups_file_name, output_dir, output_file_name, primordial_users_set):
    with open(groups_file_name, 'r') as file:
        group_list = [int(row.strip('\n').split(':')[0]) for row in file if row]

    recovery_groups_top = {}
    for group_id in group_list:
        try:
            with open('%s/%s_%d' % (output_dir, output_file_name, group_id), 'r') as file:
                members = set(int(row.strip('\n')) for row in file if row)
            top_value = len(members & primordial_users_set)
            recovery_groups_top[group_id] = {'top_value': top_value, 'members_count': len(members)}
            print('get_recovery_groups_top: group_id = %d top_value = %d' % (group_id, top_value))
        except FileNotFoundError:
            print('get_recovery_groups_top: file %s/%s_%d not found)' % (output_dir, output_file_name, group_id))
    return recovery_groups_top


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


def save_recovery_top(recovery_groups_top, pages_top, count, recovery_top_file_name):
    union_top = recovery_groups_top.copy()
    for page_id, page_info in pages_top.items():
        union_top[page_id] = page_info
    top = {}
    for group_id, group_info in union_top.items():
        top_value = group_info.get('top_value')
        top[group_id] = top_value
    top_sort = ((group_id, top[group_id]) for group_id in sorted(top, key=top.get, reverse=True))
    i = 1
    result_top = {}
    with open(recovery_top_file_name, 'w') as file:
        for group_id, top_value in top_sort:
            members_count = union_top.get(group_id).get('members_count')
            file.write('%d:%s:%d\n' % (group_id, str(members_count), top_value))
            result_top[group_id] = top_value
            i += 1
            if i > count:
                break
    return result_top