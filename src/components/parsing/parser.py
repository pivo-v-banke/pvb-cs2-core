from collections import defaultdict
from typing import Any, Optional

from demoparser2 import DemoParser as DP2

from src.components.parsing.models import MatchInfo, PlayerStatInfo, PlayerInfo


class CS2DemoInfoParser:
    def __init__(self, demo_path: str):
        self.demo_path = demo_path
        self._p = DP2(demo_path)

        self._player_info_df = None
        self._userid_to_steamid: dict[int, str] | None = None


    def _player_info_df_cached(self):
        if self._player_info_df is None:
            self._player_info_df = self._p.parse_player_info()
        return self._player_info_df

    @staticmethod
    def _first_col(df, candidates: list[str]) -> str | None:
        cols = set(getattr(df, "columns", []))
        for c in candidates:
            if c in cols:
                return c
        return None

    @staticmethod
    def _safe_str(v: Any) -> str:
        if v is None:
            return ""
        s = str(v)
        return "" if s.lower() == "nan" else s

    @staticmethod
    def _safe_int(v: Any, default: int = 0) -> int:
        try:
            if v is None:
                return default
            return int(v)
        except Exception:
            return default

    def _build_userid_map(self) -> dict[int, str]:
        if self._userid_to_steamid is not None:
            return self._userid_to_steamid

        df = self._player_info_df_cached()

        steam_col = self._first_col(df, ["steamid64", "steam_id", "steamid", "xuid"])
        userid_col = self._first_col(df, ["user_id", "userid", "userId"])

        mapping: dict[int, str] = {}
        if steam_col and userid_col:
            for _, row in df.iterrows():
                sid = self._safe_str(row.get(steam_col))
                if not sid:
                    continue
                try:
                    uid = int(row.get(userid_col))
                except Exception:
                    continue
                mapping[uid] = sid

        self._userid_to_steamid = mapping
        return mapping

    def _infer_final_score(self) -> tuple[int, int]:
        try:
            df = self._p.parse_ticks(["team_num", "team_rounds_total"])
        except Exception:
            return 0, 0

        if df is None or len(getattr(df, "index", [])) == 0:
            return 0, 0

        if "tick" not in df.columns:
            return 0, 0

        last_tick = int(df["tick"].max())
        last = df[df["tick"] == last_tick]

        if "team_num" not in last.columns or "team_rounds_total" not in last.columns:
            return 0, 0

        t_rows = last[last["team_num"] == 2]
        ct_rows = last[last["team_num"] == 3]

        t_score = int(t_rows["team_rounds_total"].max()) if len(t_rows.index) else 0
        ct_score = int(ct_rows["team_rounds_total"].max()) if len(ct_rows.index) else 0

        return t_score, ct_score

    def get_match(self) -> MatchInfo:
        df = self._player_info_df_cached()
        steam_col = self._first_col(df, ["steamid64", "steam_id", "steamid", "xuid"])
        header = self._p.parse_header()
        map_name = header.get("map_name", "unknown")

        steam_ids: list[str] = []
        if steam_col:
            steam_ids = [self._safe_str(x) for x in df[steam_col].tolist() if self._safe_str(x)]
        steam_ids = sorted(set(steam_ids))

        t_score, ct_score = self._infer_final_score()

        return MatchInfo(
            player_steam_ids=steam_ids,
            t_score=t_score,
            ct_score=ct_score,
            map_name=map_name,
        )

    def get_stats(self) -> list[PlayerStatInfo]:
        userid_to_sid = self._build_userid_map()

        try:
            df = self._p.parse_event("player_death", player=["player_steamid"], other=[])
        except TypeError:
            df = self._p.parse_event("player_death")
        except Exception:
            return []

        if df is None or len(getattr(df, "index", [])) == 0:
            return []
        def col(*cands: str) -> Optional[str]:
            cols = set(getattr(df, "columns", []))
            for c in cands:
                if c in cols:
                    return c
            return None

        attacker_sid_col = col(
            "attacker_steamid", "attacker_player_steamid", "attackerSteamid", "attacker_xuid"
        )
        victim_sid_col = col(
            "userid_steamid", "user_steamid", "victim_steamid", "userid_player_steamid", "user_player_steamid"
        )
        assister_sid_col = col(
            "assister_steamid", "assister_player_steamid", "assisterSteamid", "assister_xuid"
        )

        attacker_raw_col = col("attacker", "attacker_userid", "attacker_user_id")
        victim_raw_col = col("userid", "user_id", "victim", "victim_userid")
        assister_raw_col = col("assister", "assister_userid", "assister_user_id")

        kills = defaultdict(int)
        deaths = defaultdict(int)
        assists = defaultdict(int)

        def safe_str(v: Any) -> str:
            if v is None:
                return ""
            s = str(v)
            return "" if s.lower() == "nan" else s

        def to_steam_id(val: Any) -> Optional[str]:
            if val is None:
                return None
            s = safe_str(val)
            if not s:
                return None
            if s.isdigit() and len(s) >= 15:
                return s
            try:
                uid = int(float(s))
            except Exception:
                return None
            return userid_to_sid.get(uid)

        for _, row in df.iterrows():
            a_sid = to_steam_id(row.get(attacker_sid_col)) if attacker_sid_col else None
            v_sid = to_steam_id(row.get(victim_sid_col)) if victim_sid_col else None
            as_sid = to_steam_id(row.get(assister_sid_col)) if assister_sid_col else None

            if a_sid is None and attacker_raw_col:
                a_sid = to_steam_id(row.get(attacker_raw_col))
            if v_sid is None and victim_raw_col:
                v_sid = to_steam_id(row.get(victim_raw_col))
            if as_sid is None and assister_raw_col:
                as_sid = to_steam_id(row.get(assister_raw_col))
            if a_sid:
                kills[a_sid] += 1
            if v_sid:
                deaths[v_sid] += 1
            if as_sid:
                assists[as_sid] += 1

        all_ids = set(kills) | set(deaths) | set(assists)
        return [
            PlayerStatInfo(
                steam_id=sid,
                kills=int(kills.get(sid, 0)),
                deaths=int(deaths.get(sid, 0)),
                assists=int(assists.get(sid, 0)),
            )
            for sid in sorted(all_ids)
        ]

    def get_player_info(self, steam_id: str) -> PlayerInfo:
        df = self._player_info_df_cached()

        steam_col = self._first_col(df, ["steamid64", "steam_id", "steamid", "xuid"])
        name_col = self._first_col(df, ["name", "player_name", "display_name"])

        if not steam_col:
            return PlayerInfo(steam_id=steam_id)

        try:
            row = df.loc[df[steam_col].astype(str) == str(steam_id)].iloc[0]
        except Exception:
            return PlayerInfo(steam_id=steam_id)

        return PlayerInfo(
            steam_id=str(steam_id),
            display_name=self._safe_str(row.get(name_col)) if name_col else None,
        )
