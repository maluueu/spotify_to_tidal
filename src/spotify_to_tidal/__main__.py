import yaml
import argparse
import sys

from . import sync as _sync
from . import auth as _auth

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='config.yml', help='location of the config file')
    parser.add_argument('--uri', help='synchronize a specific URI instead of the one in the config')
    parser.add_argument('--sync-favorites', action=argparse.BooleanOptionalAction, help='synchronize the favorites')
    parser.add_argument('--sync-artists', action=argparse.BooleanOptionalAction, help='synchronize the artists')
    parser.add_argument('--sync-albums', action=argparse.BooleanOptionalAction, help='synchronize the albums')
    parser.add_argument('--sync-tidal-top100-to-playlist', action=argparse.BooleanOptionalAction, help='synchronize the Tidal top 100 to a playlist')
    args = parser.parse_args()

    sync_favorites = False
    sync_artists = False
    sync_albums = False
    sync_tidal_top100_to_playlist = False

    with open(args.config, 'r') as f:
        config = yaml.safe_load(f)
    print("Opening Spotify session")
    spotify_session = _auth.open_spotify_session(config['spotify'])
    print("Opening Tidal session")
    tidal_session = _auth.open_tidal_session()
    if not tidal_session.check_login():
        sys.exit("Could not connect to Tidal")
    if args.uri:
        # if a playlist ID is explicitly provided as a command line argument then use that
        spotify_playlist = spotify_session.playlist(args.uri)
        tidal_playlists = _sync.get_tidal_playlists_wrapper(tidal_session)
        tidal_playlist = _sync.pick_tidal_playlist_for_spotify_playlist(spotify_playlist, tidal_playlists)
        _sync.sync_playlists_wrapper(spotify_session, tidal_session, [tidal_playlist], config)
        sync_favorites = args.sync_favorites # only sync favorites if command line argument explicitly passed
        sync_artists = args.sync_artists # only sync artists if command line argument explicitly passed
        sync_albums = args.sync_albums # only sync albums if command line argument explicitly passed
        sync_tidal_top100_to_playlist = args.sync_tidal_top100_to_playlist # only sync Tidal top 100 to playlist if command line argument explicitly passed
    elif args.sync_favorites:
        sync_favorites = True # sync only the favorites
    elif args.sync_artists:
        sync_artists = True # sync only the artists
    elif args.sync_albums:
        sync_albums = True # sync only the albums
    elif args.sync_tidal_top100_to_playlist:
        sync_tidal_top100_to_playlist = True # sync the Tidal top 100 to a playlist
    elif config.get('sync_playlists', None):
        # if the config contains a sync_playlists list of mappings then use that
        _sync.sync_playlists_wrapper(spotify_session, tidal_session, _sync.get_playlists_from_config(spotify_session, tidal_session, config), config)
        sync_favorites = args.sync_favorites is None and config.get('sync_favorites_default', True)
        sync_artists = args.sync_artists is None and config.get('sync_artists_default', False)
        sync_albums = args.sync_albums is None and config.get('sync_albums_default', False)
    else:
        # otherwise sync all the user playlists in the Spotify account and favorites unless explicitly disabled
        _sync.sync_playlists_wrapper(spotify_session, tidal_session, _sync.get_user_playlist_mappings(spotify_session, tidal_session, config), config)
        sync_favorites = args.sync_favorites is None and config.get('sync_favorites_default', True)
        sync_artists = args.sync_artists is None and config.get('sync_artists_default', False)
        sync_albums = args.sync_albums is None and config.get('sync_albums_default', False)

    # Sync favorites
    if sync_favorites:
        _sync.sync_favorites_wrapper(spotify_session, tidal_session, config)

    # Sync artists
    if sync_artists:
        _sync.sync_artists_wrapper(spotify_session, tidal_session, config)

    # Sync albums
    if sync_albums:
        _sync.sync_albums_wrapper(spotify_session, tidal_session, config)

    # Sync Tidal top 100 to playlist
    if sync_tidal_top100_to_playlist:
        print(config.get('sync_tidal_top100_to_playlist_id', None))
        if config.get('sync_tidal_top100_to_playlist_id', None) is (None or "playlist_id_here"):
            print("No Tidal top 100 playlist ID configured, skipping sync")
            sys.exit(1)
        else:
            _sync.sync_tidal_top100_to_playlist_wrapper(spotify_session, tidal_session, config)

if __name__ == '__main__':
    main()
    sys.exit(0)
