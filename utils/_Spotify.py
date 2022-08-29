"""

DISCLAMER: THIS CODE IS NOT WRITEN BY ME. THIS CODE BELONGS TO DEVOXIN.
I WILL CREATE MY OWN CODE FOR THIS AS SOON AS I FIGURE OUT HOW TO DO IT.

"""


import re
from base64 import b64encode
from lavalink.models import DeferredAudioTrack, LoadResult, LoadType, PlaylistInfo, Source
from utils import _requests

ARTIST_URI_REGEX = re.compile(r'^(?:https?://(?:open\.)?spotify\.com|spotify)([/:])artist\1([a-zA-Z0-9]+)')
TRACK_URI_REGEX = re.compile(r'^(?:https?://(?:open\.)?spotify\.com|spotify)([/:])track\1([a-zA-Z0-9]+)')
PLAYLIST_URI_REGEX = re.compile(r'^(?:https?://(?:open\.)?spotify\.com(?:/user/[a-zA-Z0-9_]+)?|spotify)([/:])playlist\1([a-zA-Z0-9]+)')
ALBUM_URI_REGEX = re.compile(r'^(?:https?://(?:open\.)?spotify\.com|spotify)([/:])album\1([a-zA-Z0-9]+)')


class LoadError(Exception):
    pass


class SpotifyAudioTrack(DeferredAudioTrack):
    @classmethod
    def from_dict(cls, metadata):
        return cls({
            'identifier': metadata['id'],
            'title': metadata['name'],
            'author': metadata['artists'][0]['name'],
            'length': metadata['duration_ms'],
            'uri': f'https://open.spotify.com/track/{metadata["id"]}',
            'isSeekable': True,
            'isStream': False
        }, requester=0)

    @classmethod
    def from_items(cls, items):
        return list(map(cls.from_dict, items))

    async def load(self, client):
        result = await client.get_tracks(f'ytmsearch:{self.title} {self.author}')

        if result.load_type != LoadType.SEARCH or not result.tracks:
            raise LoadError(result.load_type.value)

        b64 = result.tracks[0].track
        self.track = b64
        return b64


class SpotifySource(Source):
    def __init__(self, client_id, client_secret):
        super().__init__('spotify')
        self._creds = b64encode(f'{client_id}:{client_secret}'.encode()).decode()
        self._token = None

    async def _req_endpoint(self, url, query=None, is_retry: bool = False):
        if not self._token:
            res = await _requests.post('https://accounts.spotify.com/api/token',
                                  headers={'Authorization': f'Basic {self._creds}', 'Content-Type': 'application/x-www-form-urlencoded'},
                                  data={'grant_type': 'client_credentials'},
                                  json=True)
            if not res:
                raise LoadError('Token failed to refresh!')
            self._token = res['access_token']

        base_req = _requests.get(f'https://api.spotify.com/v1/{url}',
                                params=query,
                                headers={'Authorization': f'Bearer {self._token}'})
        res = await base_req.json()

        if not res:
            status = await base_req.status()

            if status == 401 and not is_retry:
                self._token = None
                return await self._req_endpoint(url, query, is_retry=True)

            raise LoadError('Spotify API did not return a valid response!')

        return res

    async def load_item(self, client, query, offset: int=0):
        if query.startswith('spsearch:'):
            res = await self._req_endpoint('search', query={'q': query[9:], 'type': 'track', 'limit': 10})
            return LoadResult(LoadType.SEARCH, SpotifyAudioTrack.from_items(res['tracks']['items']))

        if (matcher := TRACK_URI_REGEX.match(query)):
            track_id = matcher.group(2)
            res = await self._req_endpoint(f'tracks/{track_id}')
            return LoadResult(LoadType.TRACK,[SpotifyAudioTrack.from_dict(res)])

        if (matcher := PLAYLIST_URI_REGEX.match(query)):
            playlist_id = matcher.group(2)
            playlist = await self._req_endpoint(f'playlists/{playlist_id}')
            tracks = await self._req_endpoint(f'playlists/{playlist_id}/tracks?offset={offset}')
            return LoadResult(LoadType.PLAYLIST,
                            SpotifyAudioTrack.from_items(map(lambda item: item['track'], tracks['items'])),
                            PlaylistInfo(playlist['name']))

        if (matcher := ARTIST_URI_REGEX.match(query)):
            artist_id = matcher.group(2)
            artist = await self._req_endpoint(f'artists/{artist_id}')
            top_tracks = await self._req_endpoint(f'artists/{artist_id}/top-tracks', query={'market': 'GB'})
            return LoadResult(LoadType.PLAYLIST,
                            SpotifyAudioTrack.from_items(top_tracks['tracks']),
                            PlaylistInfo(f'{artist["name"]}\'s Top Tracks'))

        if (matcher := ALBUM_URI_REGEX.match(query)):
            album_id = matcher.group(2)
            album = await self._req_endpoint(f'albums/{album_id}')
            tracks = await self._req_endpoint(f'albums/{album_id}/tracks?offset={offset}')
            return LoadResult(LoadType.PLAYLIST,
                            SpotifyAudioTrack.from_items(map(lambda item: item, tracks['items'])),
                            PlaylistInfo(album['name']))

        return None