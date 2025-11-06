from pydantic import BaseModel


class Config(BaseModel):
    live_shiro_uid: int = -1
    live_shiro_shiro_qid: int = -1
    live_shiro_group_ids: list[int] = []
    live_shiro_sleep_clock_hour: int = 1
    live_shiro_sleep_clock_minute: int = 0
    live_shiro_twitch_url: str = ""
    live_shiro_discord_url: str = ""
    live_shiro_steam_friend_code: int = -1

