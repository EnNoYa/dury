import requests
import re
import os
from typing import List, Optional, Union, Dict, Any

from dury.utils import distributed_download


class TwitchClient():
    PUBLIC_API_URL = "https://api.twitch.tv/helix"
    OAUTH_URL = "https://id.twitch.tv/oauth2/token"
    PLAYLISTS_URL = "https://usher.ttvnw.net/vod/{}"
    PRIVATE_API_URL = "https://gql.twitch.tv/gql"

    def __init__(self, client_id: str, client_secret: str) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.oauth = self.get_oauth()
        self.headers = {
            "Client-Id": self.client_id,
            "Authorization": self.oauth
        }

    def get_oauth(self):
        res = requests.post(self.OAUTH_URL, params={
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials"
        })
        oauth = res.json()
        return f"{oauth['token_type'].capitalize()} {oauth['access_token']}"

    def get_users(
        self, *,
        id: Optional[Union[str, List[str]]] = [],
        login: Optional[Union[str, List[str]]] = []
    ):
        params = { "id": id, "login": login }
        users = self._create_request("users", params)["data"]
        return users

    def get_channel_information(self, broadcaster_id: Union[str, List[str]]):
        params = { "broadcaster_id": broadcaster_id }
        channel_information = self._create_request("channels", params)["data"]
        return channel_information

    def get_channel_emotes(self, broadcaster_id: str):
        params = { "broadcaster_id": broadcaster_id }
        channel_emotes = self._create_request("chat/emotes", params)["data"]
        return channel_emotes

    def get_channel_chat_badges(self, broadcaster_id: str):
        params = { "broadcaster_id": broadcaster_id }
        channel_emotes = self._create_request("chat/badges", params)["data"]
        return channel_emotes

    def get_clips(
        self,
        broadcaster_id: str, *,
        after: Optional[str] = None,
        before: Optional[str] = None,
        first: Optional[int] = 20
    ):
        params = { "broadcaster_id": broadcaster_id, "first": first }
        if after is not None:
            params.update({ "after": after })
        if before is not None:
            params.update({ "before": before })

        res = self._create_request("clips", params)
        clips = res["data"]
        pagination = res["pagination"]
        return clips, pagination
    
    def get_top_games(self, *,
        after: Optional[str] = None,
        before: Optional[str] = None,
        first: Optional[int] = 20
    ):
        params = { "first": first }
        if after is not None:
            params.update({ "after": after })
        if before is not None:
            params.update({ "before": before })

        res = self._create_request("games/top", params)
        top_games = res["data"]
        pagination = res["pagination"]
        return top_games, pagination

    def get_games(self, game_id: Union[str, List[str]]):
        params = { "id": game_id }
        games = self._create_request("games", params)["data"]
        return games

    def get_streams(self, *,
        after: Optional[str] = None,
        before: Optional[str] = None,
        first: Optional[int] = 20,
        game_id: Optional[Union[str, List[str]]] = [],
        user_id: Optional[Union[str, List[str]]] = [],
        user_login: Optional[Union[str, List[str]]] = [],
    ):
        params = { "game_id": game_id, "user_id": user_id, "user_login": user_login, "first": first }
        if after is not None:
            params.update({ "after": after })
        if before is not None:
            params.update({ "before": before })

        res = self._create_request("streams", params)
        streams = res["data"]
        pagination = res["pagination"]
        return streams, pagination

    def check_broadcaster_subscription(self):
        pass

    def check_user_subscription(self):
        pass

    def get_all_stream_tags(self):
        pass

    def get_stream_tags(self):
        pass

    def get_teams(self):
        pass

    def get_user_follows(self):
        pass

    def get_videos(
        self,
        user_id: str, *,
        after: Optional[str] = None,
        before: Optional[str] = None,
        first: Optional[int] = 20
    ):
        params = { "user_id": user_id, "first": first }
        if after is not None:
            params.update({ "after": after })
        if before is not None:
            params.update({ "before": before })

        res = self._create_request("videos", params)
        videos = res["data"]
        pagination = res["pagination"]
        return videos, pagination

    def download_video(
        self,
        video_id: str, *,
        bitrate: Optional[str] = "720p60",
        output_dir: Optional[str] = "video",
        video_name: Optional[str] = None 
    ):
        assert bitrate in [
            '160p30', '360p30', '480p30', '720p30',
            '720p60', 'audio_only', 'chunked'
        ], "Invalid bitrate"

        os.makedirs(output_dir, exist_ok=True)

        access_token = self._get_access_token(video_id)["videoPlaybackAccessToken"]
        video_uri = self._get_video_uri(video_id, access_token, bitrate=bitrate)

        chunk_uris = self._get_chunk_uris(video_uri)

        if video_name is None:
            video_name = video_id
        out_path = os.path.join(output_dir, f"{video_name}_{bitrate}.mp4")
        status = distributed_download(chunk_uris, out_path)
        return status

    def _get_access_token(self, video_id: str):
        query = """
            {{
                videoPlaybackAccessToken(
                    id: {video_id},
                    params: {{
                        platform: "web",
                        playerBackend: "mediaplayer",
                        playerType: "site"
                    }}
                ) {{
                    signature
                    value
                }}
            }}
        """
        query = query.format(video_id=video_id)
        headers = { "Client-ID": "kimne78kx3ncx6brgo4mv6wki5h1ko" }
        res = requests.post(self.PRIVATE_API_URL, json={"query": query}, headers=headers)
        access_token = res.json()["data"]
        return access_token

    def _get_video_uri(
        self,
        video_id: str,
        access_token: Dict[str, Any], *,
        bitrate: Optional[str] = "720p60"
    ):
        playlists_url = self.PLAYLISTS_URL.format(video_id)
        res = requests.get(playlists_url, params={
            "nauthsig": access_token["signature"],
            "nauth": access_token["value"],
            "allow_source": "true",
            "player": "twitchweb",
            "allow_spectre": "true",
            "allow_audio_only": "true"
        })
        playlists = res.text.split("\n")
        video_uri = list(filter(lambda x: x[:5] == "https" and bitrate in x, playlists))[0]
        return video_uri

    def _get_chunk_uris(self, video_uri: str):
        res = requests.get(video_uri)
        chunk_list = res.text.split("\n")
        chunk_list = list(filter(lambda x: re.match("(\w|\d)+\.ts", x), chunk_list))

        base_url = os.path.dirname(video_uri)
        chunk_uris = [ f"{base_url}/{chunk}" for chunk in chunk_list ]
        return chunk_uris

    def _create_request(self, path: str, params: Dict[str, Any]):
        res = requests.get(
            f"{self.PUBLIC_API_URL}/{path}",
            params=params,
            headers=self.headers
        )
        return res.json()


class TwitchCrawler():

    def __init__(self, cfg) -> None:
        pass
