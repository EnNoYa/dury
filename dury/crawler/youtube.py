from typing import Optional

from pytube import YouTube, streams

from .base import APIWrapper


class YouTubeClient(APIWrapper):
    PUBLIC_API_URL = "https://www.googleapis.com/youtube/v3"

    def __init__(
        self,
        api_key: str
    ) -> None:
        self.api_key = api_key
        super(YouTubeClient, self).__init__(self.PUBLIC_API_URL)

    def get_activities(
        self,
        channel_id: str, *,
        max_results: Optional[int] = 5,
        page_token: Optional[str] = None,
        published_after: Optional[str] = None,
        published_before: Optional[str] = None,
        region_code: Optional[str] = None
    ):
        params = {
            "key": self.api_key,
            "part":  "id, snippet, contentDetails",
            "channelId": channel_id,
            "maxResults": max_results,
            "pageToken": page_token,
            "publishedAfter": published_after,
            "publishedBefore": published_before,
            "regionCode": region_code
        }
        res = self._get("activities", params=params)
        return res

    def get_channels(
        self, *,
        category_id: Optional[str] = None,
        for_username: Optional[str] = None,
        id: Optional[str] = None, # "id01, id02, ..."
        max_results: Optional[int] = 5,
        page_token: Optional[str] = None
    ):
        params = {
            "key": self.api_key,
            "part": "id, snippet, contentDetails, statistics",
            "categoryId": category_id,
            "forUsername": for_username,
            "id": id,
            "maxResults": max_results,
            "pageToken": page_token
        }
        res = self._get("channels", params=params)
        return res

    def get_comments(
        self, *,
        id: Optional[str] = None,
        parent_id: Optional[str] = None,
        max_results: Optional[int] = 5,
        page_token: Optional[str] = None,
        text_format: Optional[str] = "plainText"
    ):
        params = {
            "key": self.api_key,
            "part": "id, snippet",
            "id": id,
            "parentId": parent_id,
            "maxResults": max_results,
            "pageToken": page_token,
            "textFormat": text_format
        }
        res = self._get("comments", params=params)
        return res
    
    def get_comment_threads(
        self, *,
        all_threads_related_to_channel_id: Optional[str] = None,
        channel_id: Optional[str] = None,
        id: Optional[str] = None,
        video_id: Optional[str] = None,
        max_results: Optional[int] = 5,
        page_token: Optional[str] = None,
        search_terms: Optional[str] = None,
        text_format: Optional[str] = "plainText"
    ):
        params = {
            "key": self.api_key,
            "part": "id, replies, snippet",
            "allThreadsRelatedToChannelId": all_threads_related_to_channel_id,
            "channel_id": channel_id,
            "id": id,
            "videoId": video_id,
            "maxResults": max_results,
            "pageToken": page_token,
            "searchTerms": search_terms,
            "textFormat": text_format
        }
        res = self._get("commentThreads", params=params)
        return res

    def get_guide_categories(
        self, *,
        id: Optional[str] = None,
        region_code: Optional[str] = None,
        hl: Optional[str] = "ko-KR"
    ):
        params = {
            "key": self.api_key,
            "part": "id, snippet",
            "id": id,
            "regionCode": region_code,
            "hl": hl
        }
        res = self._get("guideCategories", params=params)
        return res

    def get_playlists(
        self, *,
        channel_id: Optional[str] = None,
        id: Optional[str] = None,
        max_results: Optional[int] = 5,
        page_token: Optional[str] = None
    ):
        params = {
            "key": self.api_key,
            "part": "id, snippet, status",
            "channel_id": channel_id,
            "id": id,
            "maxResults": max_results,
            "pageToken": page_token
        }
        res = self._get("playlists", params=params)
        return res

    def get_video_categories(
        self, *,
        id: Optional[str] = None,
        region_code: Optional[str] = None,
        hl: Optional[str] = "ko-KR"
    ):
        params = {
            "key": self.api_key,
            "part": "id, snippet",
            "id": id,
            "regionCode": region_code,
            "hl": hl
        }
        res = self._get("videoCategories", params=params)
        return res

    def get_videos(
        self, *,
        chart: Optional[str] = None,
        id: Optional[str] = None,
        max_results: Optional[int] = 5,
        page_token: Optional[str] = None,
        region_code: Optional[str] = None,
        video_category_id: Optional[str] = None
    ):
        params = {
            "key": self.api_key,
            "part": "id, snippet, contentDetails, liveStreamingDetails, player, recordingDetails, statistics, status, topicDetails",
            "chart": chart,
            "id": id,
            "maxResults": max_results,
            "pageToken": page_token,
            "regionCode": region_code,
            "videoCategoryId": video_category_id
        }
        res = self._get("videos", params=params)
        return res


    def search(
        self, *,
        related_to_video_id: Optional[str] = None,
        channel_id: Optional[str] = None,
        channel_type: Optional[str] = None, # any, show
        event_type: Optional[str] = None, # completed, live, upcoming
        max_results: Optional[int] = 5,
        page_token: Optional[str] = None,
        order: Optional[str] = "relevance", # date, rating, relevance, title, videoCount, viewCount
        published_after: Optional[str] = None,
        published_before: Optional[str] = None,
        q: Optional[str] = None,
        region_code: Optional[str] = None,
        safe_search: Optional[str] = "none", # moderate, none, strict
        topic_id: Optional[str] = None,
        type: Optional[str] = None, # channel, playlist, video
        video_caption: Optional[str] = "any", # any, closedCaption, none
        video_definition: Optional[str] = "any", # any, high, standard
        video_category_id: Optional[str] = None,
        video_dimension: Optional[str] = "any", # 2d, 3d, any
        video_duration: Optional[str] = "any", # any, long, medium, short
        video_embeddable: Optional[str] = "any", # any, true
        video_license: Optional[str] = "any", # any, creativeCommon, youtube
        video_syndicated: Optional[str] = "any", # any, true
        video_type: Optional[str] = "any" # any, episode, movie
    ):
        params = {
            "key": self.api_key,
            "relatedToVideoId": related_to_video_id,
            "channelId": channel_id,
            "channelType": channel_type,
            "eventType": event_type,
            "maxResults": max_results,
            "pageToken": page_token,
            "order": order,
            "publishedAfter": published_after,
            "publishedBefore": published_before,
            "q": q,
            "regionCode": region_code,
            "safeSearch": safe_search,
            "topicId": topic_id,
            "type": type,
            "videoCaption": video_caption,
            "videoCategoryId": video_category_id,
            "videoDefinition": video_definition,
            "videoDimension": video_dimension,
            "videoDuration": video_duration,
            "videoEmbeddable": video_embeddable,
            "videoLicense": video_license,
            "videoSyndicated": video_syndicated,
            "videoType": video_type
        }
        res = self._get("search", params=params)
        return res

    def download(
        self,
        video_url: str,
        output_dir: str, *,
        filename: Optional[str] = None,
        prefix: Optional[str] = None,
        option: Optional[str] = "lowest"
    ) -> str:
        streams = YouTube(video_url).streams
        if option == "audio_only":
            stream = streams.get_audio_only()
        elif option in ("1080p", "720p", "480p", "360p", "240p", "144p" ):
            stream = streams.get_by_resolution(option)
        elif option == "highest":
            stream = streams.get_highest_resolution()
        elif option == "lowest":
            stream = streams.get_lowest_resolution()
        else:
            raise NotImplementedError

        return stream.download(output_dir, filename=filename, filename_prefix=prefix)
