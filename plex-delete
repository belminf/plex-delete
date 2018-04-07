#!/usr/bin/env python3

from __future__ import print_function

import xml.dom.minidom
import sys
import argparse

try:
    import urllib.request as urllib2
    from urllib.error import HTTPError
except:
    import urllib2
    from urllib2 import HTTPError


def make_url(args, path):
    composed_url = "http://{server}:{port}".format(**args) + path
    token_param = 'X-Plex-Token={token}'.format(**args)
    return ''.join((composed_url, '&' if '?' in composed_url else '?', token_param))


def get_libraries(args):
    libary_dom = xml.dom.minidom.parse(urllib2.urlopen(make_url(args, '/library/sections')))
    libraries = libary_dom.getElementsByTagName('Directory')
    return {l.getAttribute('key'): l.getAttribute('title') for l in libraries}


def get_watched(args, library_id):
    videos_dom = xml.dom.minidom.parse(urllib2.urlopen(make_url(args, '/library/sections/{library_id}/all?type=4'.format(library_id=library_id))))
    videos = videos_dom.getElementsByTagName('Video')
    return {v.getAttribute('ratingKey'): {
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
    for id, show in sorted(get_watched(args, target_library).items()):
        print('Deleting {show}: S{season},E{episode}...'.format(**show))
        delete_video(args, id)


def main():
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

    args = vars(parser.parse_args())

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
