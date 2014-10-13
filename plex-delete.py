import xml.dom.minidom
import sys
import argparse
import urllib.request as request
import urllib
import pprint

def make_url(args, path):
    return("http://{server}:{port}".format(**args) + path)

def get_libraries(args):
    libary_dom = xml.dom.minidom.parse(request.urlopen(make_url(args,'/library/sections')))
    libraries = libary_dom.getElementsByTagName('Directory')
    return {l.getAttribute('key'):l.getAttribute('title') for l in libraries}

def get_watched(args, library_id):
    videos_dom = xml.dom.minidom.parse(request.urlopen(make_url(args,'/library/sections/{library_id}/all?type=4'.format(library_id=library_id))))
    videos = videos_dom.getElementsByTagName('Video')
    return {v.getAttribute('ratingKey'):{
            'show': v.getAttribute('grandparentTitle'),
            'season': v.getAttribute('parentIndex'),
            'episode': v.getAttribute('index'),
            'viewed_at': v.getAttribute('lastViewedAt'),
        } for v in videos if v.getAttribute('viewCount')}

def delete_video(args, media_id):
    opener = request.build_opener(urllib.request.HTTPHandler)
    this_request = request.Request(make_url(args, '/library/metadata/{0}'.format(media_id)))
    this_request.get_method = lambda: 'DELETE'
    url = opener.open(this_request)

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
    for id, show in get_watched(args, target_library).items():
        print('- {show}: S{season},E{episode}'.format(**show))

def delete_watched(args, target_library):
    print('')
    for id, show in get_watched(args, target_library).items():
        print('- Deleting "{show}" S{season},E{episode}...'.format(**show))
        delete_video(args, id)
    print('Done.')
        
def main():
    parser = argparse.ArgumentParser(description='Uses HTTP API to interact with your Plex libraries.')
    group_config = parser.add_argument_group('configuration')
    group_config.add_argument(
        '-s',
        dest='server',
        default='127.0.0.1',
        help='Plex server\'s IP or DNS hostname (DEFAULT: 127.0.0.1)'
    )
    group_config.add_argument(
        '-p',
        dest='port',
        default='32400',
        help='Plex server\'s port number (DEFAULT: 32400)'
    )
    group_config.add_argument(
        '-l',
        metavar='LIBRARY_ID',
        dest='target_library',
        default='1',
        help='library to target (DEFAULT: 1)'
    )
        
    group_list = parser.add_argument_group('informational')
    group_list.add_argument(
        '--list-libraries',
        dest='list_libraries',
        action='store_true',
        help='list libraries available'
    )
    group_list.add_argument(
        '--list-watched',
        dest='list_watched',
        action='store_true',
        help='list watched videos'
    )

    group_modify = parser.add_argument_group('modifications')
    group_modify.add_argument(
        '--delete-watched',
        dest='delete_watched',
        action='store_true',
        help='delete watched videos'
    )

    args = vars(parser.parse_args())

    if sum(args['list_libraries'], args['list_watched'], args['delete_watched']) != 1:
        parser.print_help
    elif args['list_libraries']:
        list_libraries(args)
    elif args['list_watched']:
        list_watched(args, args['target_library'])
    elif args['delete_watched']:
        delete_watched(args, args['target_library'])
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
