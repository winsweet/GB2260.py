#!/usr/bin/env python
# coding: utf-8

"""
A script to generate the data module.
"""

from __future__ import print_function, unicode_literals
import os
import sys
import re

LATEST_YEAR = 2014
MINORITY_RULE = re.compile(
        r'(.*?)(?:(?:(?:蒙古|回|藏|维吾尔|苗|彝|壮|布依|朝鲜|'
        r'满|侗|瑶|白|土家|哈尼|哈萨克|傣|黎|傈僳|佤|畲|拉祜|'
        r'水|东乡|纳西|景颇|柯尔克孜|土|达斡尔|仫佬|羌|布朗|'
        r'撒拉|毛南|仡佬|锡伯|阿昌|普米|塔吉克|怒|乌兹别克|'
        r'俄罗斯|鄂温克|德昂|保安|裕固|京|塔塔尔|独龙|鄂伦春|'
        r'赫哲|门巴|珞巴|基诺|高山)族)+)自治(?:县|州|旗)')


def get_name_suffix(path):
    path, _ = os.path.splitext(path)
    splited = path.rsplit('-', 1)
    if len(splited) == 2:
        return splited[-1]
    return ''


def ensure_unicode(text):
    if isinstance(text, bytes):
        return text.decode('utf-8')
    return text


def get_alias(name):
    if name == u'县' or name == u'市辖区':
        return ''
    if name[-3:-1] == u'自治':
        alias = MINORITY_RULE.findall(name)
        if alias and alias[0]:
            return alias[0]
    if len(name) >= 4 and (name[-2:] == u'地区' or name[-2:] == u'新区'):
        return name[:-2]
    if name[:2] == u'香港' or name[:2] == u'澳门':
        return name[:2]
    if (len(name) > 2 and
            (name[-1] == u'县' or name[-1] == u'区' or name[-1] == u'市')):
        return name[:-1]
    return ''


def index_insert(name, code, year, index):
    if name == u'县' or name == u'市辖区':
        return
    if name not in index:
        index[name] = {}
    if code not in index[name] or year is None:
        index[name][code] = year
        return
    if not index[name][code]:
        return
    cur_year = year if year > 3000 else year * 100 + 12
    max_year = index[name][code]
    max_year = max_year if max_year > 3000 else max_year * 100 + 12
    if cur_year > max_year:
        index[name][code] = year
    return


def make_value_key(value):
    if value[1] is None:
        return (LATEST_YEAR, 12, value[0])
    if value[1] < 3000:
        return (value[1], 12, value[0])
    return (value[1] / 100, value[1] % 100, value[0])


def main():
    if len(sys.argv) < 3:
        print('Usage: {.argv[0]} [A] [B] ... [DESTINATION]'.format(sys),
              file=sys.stderr)
        sys.exit(1)
    source = sys.argv[1:-1]
    destination = sys.argv[-1]

    data = {}
    index = {}
    for current_source in source:
        suffix = get_name_suffix(current_source)
        year = int(suffix) if suffix else None
        current_dict = data.setdefault(year, {})

        with open(current_source, 'r') as source_file:
            for line in source_file:
                code, name = line.strip().split()
                name = ensure_unicode(name)
                current_dict[int(code)] = name

                index_insert(name, int(code), year, index)
                alias = get_alias(name)
                if alias:
                    index_insert(alias, int(code), year, index)

    for key, value in index.iteritems():
        index[key] = sorted(
                value.items(), key=lambda x: make_value_key(x), reverse=True)

    result = 'LATEST_YEAR = {0}\ndata = {1}\nindex = {2}'.format(
            LATEST_YEAR, repr(data), repr(index))
    with open(destination, 'w') as destination_file:
        print(result, file=destination_file)

    for current_dict in data.values():
        message = '{0} records has been generated.'.format(len(current_dict))
        print(message, file=sys.stderr)


if __name__ == '__main__':
    main()
