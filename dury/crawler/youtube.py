from typing import Optional

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
            "part": "id, snippet, brandingSettings, contentDetails, invideoPromotion, statistics, topicDetails",
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
            "part": "id, snippet, contentDetails, fileDetails, liveStreamingDetails, player, processingDetails, recordingDetails, statistics, status, suggestions, topicDetails",
            "chart": chart,
            "id": id,
            "maxResults": max_results,
            "pageToken": page_token,
            "regionCode": region_code,
            "videoCategoryId": video_category_id
        }
        res = self._get("videos", params=params)
        return res
