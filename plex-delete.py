#!/usr/bin/env python3

from __future__ import print_function

import xml.dom.minidom
import os
import sys
import argparse
import collections
import json

try:
    import urllib.request as urllib2
    from urllib.error import HTTPError
except:
    import urllib2
    from urllib2 import HTTPError

CONFIG_FILE = os.path.expanduser('~/.plex-delete.json')
ACTION_MESSAGE = '''
Would you like to delete watched episodes from series {show}?
- (a)lways delete watched files from series {show}
- (n)ever delete watched files from series {show}
- (r)emove all {count} watched files from {show}
- (i)nteractively delete watched files from {show}
- (s)kip {show} this time
- (q)uit the program
'''


class SetJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return sorted(obj)
        return json.JSONEncoder.defaut(self, obj)


def read_config(filename):
    config = {
        'always_delete': [],
        'always_ignore': [],
    }

    if os.path.isfile(filename):
        with open(filename) as fh:
            config.update(json.load(fh))

    config['always_delete'] = set(config['always_delete'])
    config['always_ignore'] = set(config['always_ignore'])
    return config


def write_config(filename, config):
    with open(filename, 'w') as fh:
        json.dump(config, fh, cls=SetJsonEncoder)


def add_always_delete(args, show, episodes):
    config = args['config']
    config['always_delete'].add(show)
    config['always_ignore'].discard(show)
    write_config(CONFIG_FILE, config)

    return delete_all(args, show, episodes)


def add_always_ignore(args, show, episodes):
    config = args['config']
    config['always_ignore'].add(show)
    config['always_delete'].discard(show)
    write_config(CONFIG_FILE, config)

    return True


def delete_all(args, show, episodes, interactive=False):
    for id, episode in sorted(episodes):
        if interactive:
            key = ''
            while key not in 'yn':
                key = raw_input('Remove "{show}" S{season},E{episode}? (y/n)'
                                .format(**episode)).lower()

        else:
            key = 'y'

        if key == 'y':
            print(' - Removing "{show}" S{season},E{episode}...'
                  .format(**episode))
            delete_video(args, id)
        else:
            print(' - Skipping "{show}" S{season},E{episode}...'
                  .format(**episode))

    return True

def delete_all_interactive(args, show, episodes):
    return delete_all(args, show, episodes, interactive=True)


def skip(args, show, episodes):
    return True


def quit(args, show, episodes):
    sys.exit(0)


ACTION_KEYS = dict(
    a=add_always_delete,
    n=add_always_ignore,
    r=delete_all,
    i=delete_all_interactive,
    s=skip,
    q=quit,
)


def make_url(args, path):
    composed_url = "http://{server}:{port}".format(**args) + path
    token_param = 'X-Plex-Token={token}'.format(**args)
    return ''.join((composed_url, '&' if '?' in composed_url else '?', token_param))


def get_libraries(args):
    libary_dom = xml.dom.minidom.parse(urllib2.urlopen(make_url(args,'/library/sections')))
    libraries = libary_dom.getElementsByTagName('Directory')
    return {l.getAttribute('key'):l.getAttribute('title') for l in libraries}


def get_watched(args, library_id):
    videos_dom = xml.dom.minidom.parse(urllib2.urlopen(make_url(args,'/library/sections/{library_id}/all?type=4'.format(library_id=library_id))))
    videos = videos_dom.getElementsByTagName('Video')
    return {v.getAttribute('ratingKey'):{
        'show': v.getAttribute('grandparentTitle'),
        'season': v.getAttribute('parentIndex'),
        'episode': v.getAttribute('index'),
        'viewed_at': v.getAttribute('lastViewedAt'),
    } for v in videos if v.getAttribute('viewCount')}


def delete_video(args, media_id):
    opener = urllib2.build_opener(urllib2.HTTPHandler)
    this_request = urllib2.Request(make_url(args, '/library/metadata/{0}'.format(media_id)))
    this_request.get_method = lambda: 'DELETE'
    try:
        opener.open(this_request)
    except HTTPError as e:
        if e.code == 403:
            print('')
            print('DELETION ERROR: Client delete disabled on Plex server?')
            sys.exit()
        raise



def list_libraries(args):
    print('')
    print('Plex Libraries:')
    print('---------------')
    for id, title in get_libraries(args).items():
        print(id + ') ' + title)


def list_watched(args, target_library):
    print('')
    print('Watched in Library: {0}'.format(target_library))
    print('-------------------')
    for id, show in sorted(get_watched(args, target_library).items()):
        print('- {show}: S{season},E{episode}'.format(**show))


def delete_watched(args, target_library, force):
    print('')
    shows = collections.defaultdict(list)
    for id, show in sorted(get_watched(args, target_library).items()):
        shows[show['show']].append((id, show))

    for show, episodes in sorted(shows.items()):
        print('Show: %s' % show)
        if force or show in args['config']['always_delete']:
            print('In always delete list, removing episodes')
            delete_all(args, show, episodes)
            continue

        elif show in args['config']['always_ignore']:
            print('In always ignore list, skipping')
            continue

        for id, episode in episodes:
            print(' - "{show}" S{season},E{episode}...'.format(**episode))

        print(ACTION_MESSAGE.format(
            show=show,
            count=len(episodes),
        ))

        key = ''
        while key not in ACTION_KEYS:
            key = raw_input().lower()

        ACTION_KEYS[key](args, show, episodes)


def main():
    args = dict(
        config=read_config(CONFIG_FILE),
    )

    parser = argparse.ArgumentParser(
        description='Uses HTTP API to interact with your Plex libraries.')
    group_config = parser.add_argument_group('configuration')
    group_config.add_argument(
        '--server',
        '-s',
        default='127.0.0.1',
        help='Plex server\'s IP or DNS hostname (DEFAULT: 127.0.0.1)'
    )
    group_config.add_argument(
        '--port',
        '-p',
        default='32400',
        help='Plex server\'s port number (DEFAULT: 32400)'
    )
    group_config.add_argument(
        '--target-library',
        '-l',
        metavar='LIBRARY_ID',
        default='1',
        help='library to target (DEFAULT: 1)'
    )
    group_config.add_argument(
        '--token',
        '-t',
        metavar='PLEX_TOKEN',
        help='Plex token (required, see: https://support.plex.tv/hc/en-us/articles/204059436)',
        required=True
    )

    group_list = parser.add_argument_group('informational')
    group_list.add_argument(
        '--list-libraries',
        action='store_true',
        help='list libraries available'
    )
    group_list.add_argument(
        '--list-watched',
        action='store_true',
        help='list watched videos'
    )

    group_modify = parser.add_argument_group('modifications')
    group_modify.add_argument(
        '--delete-watched',
        action='store_true',
        help='delete watched videos'
    )
    group_modify.add_argument(
        '--force',
        action='store_true',
        help='disregard config and do not confirm deletions'
    )

    args.update(vars(parser.parse_args()))

    if sum([args['list_libraries'], args['list_watched'], args['delete_watched']]) != 1:
        parser.print_help()
    elif args['list_libraries']:
        list_libraries(args)
    elif args['list_watched']:
        list_watched(args, args['target_library'])
    elif args['delete_watched'] or args['force_delete_watched']:
        delete_watched(args, args['target_library'], args['force'])
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
