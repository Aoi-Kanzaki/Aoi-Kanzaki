"""MADE BY DEVOXIN NOT ME, I AM NOT THE AUTHOR OF THIS SOURCE CODE.
ALL CREDITS GO TO DEVOXIN."""

import re
from base64 import b64encode

from lavalink.errors import LoadError
from lavalink.models import (AudioTrack, DeferredAudioTrack, LoadResult,
                             LoadType, PlaylistInfo, Source)
from utils import requests

ARTIST_URI_REGEX = re.compile(
    r'^(?:https?://(?:open\.)?spotify\.com|spotify)([/:])artist\1([a-zA-Z0-9]+)')
TRACK_URI_REGEX = re.compile(
    r'^(?:https?://(?:open\.)?spotify\.com|spotify)([/:])track\1([a-zA-Z0-9]+)')
ALBUM_URI_REGEX = re.compile(
    r'^(?:https?://(?:open\.)?spotify\.com|spotify)([/:])album\1([a-zA-Z0-9]+)')
PLAYLIST_URI_REGEX = re.compile(
    r'^(?:https?://(?:open\.)?spotify\.com(?:/user/[a-zA-Z0-9_]+)?|spotify)([/:])playlist\1([a-zA-Z0-9]+)')
EXTRANEOUS_WHITESPACE = re.compile(r'\s{2,}|\s$|^\s')
EXTRANEOUS_HYPHEN = re.compile(r'^ *\- *| *\- *$')
TITLE_SANITISE = re.compile(
    r'[(\[][^)\]]*(?:lyrics|official|music).*[)\]] ?', re.IGNORECASE)


class SpotifyAudioTrack(DeferredAudioTrack):
    @classmethod
    def from_dict(cls, metadata, **kwargs):
        if metadata is None:
            raise LoadError('Spotify API did not return a valid response!')
        album = metadata.get('album', kwargs.get('album'))
        extra = {
            'isrc': metadata.get('external_ids', {}).get('isrc'),
            'feat': list(map(lambda a: a['name'], metadata['artists'][1:])),
            'artwork': album['images'][0]['url'],
            'year': album['release_date'].split('-')[0],
            'album_name': album['name'],
            'album_url': f'https://open.spotify.com/album/{album["id"]}'
        }
        return cls({
            'identifier': metadata['id'],
            'title': metadata['name'],
            'author': metadata['artists'][0]['name'],
            'length': metadata['duration_ms'],
            'uri': f'https://open.spotify.com/track/{metadata["id"]}',
            'isSeekable': True,
            'isStream': False
        }, requester=0, **extra)

    @classmethod
    def from_items(cls, items, **kwargs):
        return list(map(lambda item: cls.from_dict(item, **kwargs), items))

    def _clean_extraneous(self, s: str) -> str:
        s = EXTRANEOUS_WHITESPACE.sub('', s)
        s = EXTRANEOUS_HYPHEN.sub('', s)
        return s

    def _prioritise(self, external: AudioTrack) -> int:
        self_lowered = self.title.lower()
        self_artist = self.author.lower()
        lowered = external.title.lower()
        artist = external.author.replace('- Topic', '').lower()

        if self_artist in lowered:
            lowered = lowered.replace(self_artist, '')

        score = 0

        if lowered == self_lowered:
            score += 3

        if artist == self_artist:
            score += 3

        if 'remix' in lowered:
            if 'remix' in self_lowered:
                score += 3
            else:
                score -= 5
        else:
            if any(word in lowered for word in ('audio', 'radio')):
                score += 3
            elif 'lyrics' in lowered:
                # Lyrics might be sped up due to people trying to evade CID.
                score += 2

        if external.author.endswith('- Topic'):
            score += 3

        duration_distance = max(
            self.duration, external.duration) - min(self.duration, external.duration)
        duration_score = duration_distance / 3750
        score -= duration_score

        # check title keywords?
        return score

    async def load(self, client):
        set_key = 'alt:' + (self.extra['isrc'] or self.identifier)

        if not self.extra['isrc']:
            src = next(source for source in client.sources if isinstance(
                source, SpotifySource))
            tracks = (await src._load_track(track_id=self.identifier)).tracks
            if tracks:
                return await tracks[0].load(client)

            return None

        result = await client.get_tracks(f'ytsearch:"{self.extra["isrc"].replace("-", "")}"')

        if result.load_type != LoadType.SEARCH or not result.tracks:
            result = await client.get_tracks(f'ytsearch:{self.title} {self.author}')

            if result.load_type != LoadType.SEARCH or not result.tracks:
                raise LoadError(result.load_type.value)

            score = (-99999999, None)

            for track in result.tracks:
                if (track_score := self._prioritise(track)) > score[0]:
                    score = (track_score, track)

            b64 = score[1].track
        else:
            b64 = result.tracks[0].track

        self.track = b64
        return b64


class SpotifySource(Source):
    def __init__(self, clId, clSec):
        super().__init__('spotify')
        self._creds = b64encode(f'{clId}:{clSec}'.encode()).decode()
        self._token = None

    async def _refresh_oauth(self):
        res = await requests.post('https://accounts.spotify.com/api/token',
                                  headers={'Authorization': f'Basic {self._creds}',
                                           'Content-Type': 'application/x-www-form-urlencoded'},
                                  data={'grant_type': 'client_credentials'},
                                  json=True)

        if not res:
            raise LoadError('token refresh shidded pants')

        self._token = res['access_token']

    async def _req_endpoint(self, url, query=None, is_retry: bool = False):
        if not self._token:
            await self._refresh_oauth()

        base_req = requests.get(f'https://api.spotify.com/v1/{url}',
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

    async def _load_paginated(self, endpoint, offset: int = 0, **kwargs):
        body = await self._req_endpoint(f'{endpoint}?offset={offset}')
        tracks = SpotifyAudioTrack.from_items(
            map(lambda item: item.get('track', item), body['items']), **kwargs)
        if offset < body['total']:
            tracks.extend(await self._load_paginated(endpoint, offset + 100, **kwargs))
        return tracks

    async def _load_search(self, query: str):
        res = await self._req_endpoint('search', query={'q': query, 'type': 'track', 'limit': 10})
        tracks = SpotifyAudioTrack.from_items(res['tracks']['items'])
        return LoadResult(LoadType.SEARCH, tracks) if tracks else LoadResult(LoadType.NO_MATCHES, [])

    async def _load_search_artist(self, artist: str):
        res = await self._req_endpoint('search', query={'q': artist, 'type': 'artist', 'limit': 1})
        return res['artists']['items'][0]['id'] if res['artists']['items'] else None

    async def _load_artist(self, artist_id: str):
        artist = await self._req_endpoint(f'artists/{artist_id}')
        top_tracks = await self._req_endpoint(f'artists/{artist_id}/top-tracks', query={'market': 'GB'})
        return LoadResult(LoadType.PLAYLIST, SpotifyAudioTrack.from_items(top_tracks['tracks']), PlaylistInfo(f'{artist["name"]}\'s Top Tracks'))

    async def _load_track(self, track_id: str):
        res = await self._req_endpoint(f'tracks/{track_id}')
        return LoadResult(LoadType.TRACK, [SpotifyAudioTrack.from_dict(res)])

    async def _load_album(self, album_id: str):
        album = await self._req_endpoint(f'albums/{album_id}')
        tracks = await self._load_paginated(f'albums/{album_id}/tracks', album=album)
        return LoadResult(LoadType.PLAYLIST, tracks, PlaylistInfo(album['name']))

    async def _load_playlist(self, playlist_id: str):
        playlist = await self._req_endpoint(f'playlists/{playlist_id}')
        tracks = await self._load_paginated(f'playlists/{playlist_id}/tracks')
        return LoadResult(LoadType.PLAYLIST, tracks, PlaylistInfo(playlist['name']))

    async def load_recommended(self, track_ids):
        res = await self._req_endpoint('recommendations', query={'seed_tracks': ','.join(track_ids), 'market': 'GB', 'limit': 1})
        return list(map(SpotifyAudioTrack.from_dict, res['tracks']))[0]

    async def load_item(self, client, query):
        if query.startswith('spsearch:'):
            return await self._load_search(query[9:])

        if query.startswith('artist:') and (artist_id := await self._load_search_artist(query[7:])) is not None:
            return await self._load_artist(artist_id=artist_id)

        if (matcher := TRACK_URI_REGEX.match(query)):
            return await self._load_track(track_id=matcher.group(2))

        if (matcher := PLAYLIST_URI_REGEX.match(query)):
            return await self._load_playlist(playlist_id=matcher.group(2))

        if (matcher := ARTIST_URI_REGEX.match(query)):
            return await self._load_artist(artist_id=matcher.group(2))

        if (matcher := ALBUM_URI_REGEX.match(query)):
            return await self._load_album(album_id=matcher.group(2))

        return None
