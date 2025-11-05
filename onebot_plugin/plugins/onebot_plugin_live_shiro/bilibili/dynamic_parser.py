from typing import Optional

from .dynamic_type import DynamicType


class DynamicParser:
    def __init__(self, dynamic: dict) -> None:
        self.current_type = DynamicType.NONE
        self.dynamic = dynamic
        self._inner_processor = {
            DynamicType.FORWARD: self._parse_forward,
            DynamicType.AV: self._parse_av,
            DynamicType.PGC: self._parse_pgc,
            DynamicType.WORLD: self._parse_world,
            DynamicType.DRAW: self._parse_draw,
            DynamicType.ARTICLE: self._parse_article,
            DynamicType.MUSIC: self._parse_music,
            DynamicType.COMMON_SQUARE: self._parse_command_square,
            DynamicType.LIVE: self._parse_live,
            DynamicType.MEDIALIST: self._parse_medialist,
            DynamicType.COURSES_SEASON: self._parse_courses_season,
            DynamicType.LIVE_RCMD: self._parse_live_rcmd,
            DynamicType.UGC_SEASON: self._parse_ugc_season
        }

    def parse(self) -> Optional[dict]:
       return None

    def _parse_forward(self) -> dict:
        return {}
    
    def _parse_av(self) -> dict:
        return {}
    
    def _parse_pgc(self) -> dict:
        return {}
    
    def _parse_world(self) -> dict:
        return {}
    
    def _parse_draw(self) -> dict:
        return {}

    def _parse_article(self) -> dict:
        return {}
    
    def _parse_music(self) -> dict:
        return {}
    
    def _parse_command_square(self) -> dict:
        return {}
    
    def _parse_live(self) -> dict:
        return {}
    
    def _parse_medialist(self) -> dict:
        return {}
    
    def _parse_courses_season(self) -> dict:
        return {}
    
    def _parse_live_rcmd(self) -> dict:
        return {}
    
    def _parse_ugc_season(self) -> dict:
        return {}
