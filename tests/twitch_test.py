from dury.crawler.twitch import TwitchClient


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    load_dotenv()

    client_id = os.environ.get("TWITCH_CLIENT_ID")
    client_secret = os.environ.get("TWITCH_CLIENT_SECRET")

    client = TwitchClient(client_id, client_secret)

    users = client.get_users(["ddahyoni", "pjs9073"])
    user_ids = [user["id"] for user in users]
    channel_information = client.get_channel_information(user_ids)

    videos, pagination = client.get_videos(user_ids[0], first=20)
    video_id = "1081430996"

    test = client.download_video(video_id, video_name="test", bitrate="160p30")
    print("Done")
