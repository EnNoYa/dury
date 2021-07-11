from dury.crawler.twitch import TwitchClient


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    load_dotenv()

    client_id = os.environ.get("TWITCH_CLIENT_ID")
    client_secret = os.environ.get("TWITCH_CLIENT_SECRET")

    client = TwitchClient(client_id, client_secret)

    login_ids = ["ddahyoni", "pjs9073"]
    users = client.get_users(login=login_ids)
    user_ids = [user["id"] for user in users]
    channel_information = client.get_channel_information(user_ids)
    channel_emotes = client.get_channel_emotes(user_ids[0])
    channel_chat_badges = client.get_channel_chat_badges(user_ids[0])
    
    clips, clip_pagination = client.get_clips(user_ids[0])
    
    videos, video_pagination = client.get_videos(user_ids[0], first=20)
    video_id = "1081430996"
    
    top_games, game_pagination = client.get_top_games(first=20)
    game_id = top_games[0]["id"]

    games = client.get_games([top_games[0]["id"], top_games[1]["id"]])
    
    streams, stream_pagination = client.get_streams(user_login=login_ids)
    status = client.download_video(video_id, video_name="test", bitrate="160p30")
    print("Done")
