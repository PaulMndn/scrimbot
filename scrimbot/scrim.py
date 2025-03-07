from datetime import tzinfo, datetime
from typing import Optional

from scrimbot import tag


class Scrim:
    def __init__(self, data: dict, timezone: tzinfo, sync):
        self.data = data
        self.name = data.get("name", None)
        self.size = data.get("size", 8)
        self.time = datetime.fromtimestamp(data["time"], timezone)
        self.timezone = timezone
        self.author = self.data["author"]
        self.__settings: Optional[dict] = None
        self.__sync = sync

        if "players" not in self.data:
            self.data["players"] = []

        if "reserve" not in self.data:
            self.data["reserve"] = []

    @property
    def id(self):
        return self.data["thread"]

    @property
    def num_players(self):
        return len(self.data["players"])

    @property
    def num_reserves(self):
        return len(self.data["reserve"])

    @property
    def full(self) -> bool:
        return self.size <= self.num_players

    @property
    def started(self) -> bool:
        return self.data.get("started", False)

    @started.setter
    def started(self, started: bool):
        if started and "started" not in self.data:
            self.data["started"] = True
            self.__sync()
        elif not started and "started" in self.data:
            del self.data["started"]
            self.__sync()

    @property
    def settings(self):
        return self.__settings

    @settings.setter
    def settings(self, settings: dict):
        self.__settings = settings

    @property
    def __role(self):
        return None if self.__settings is None or "role" not in self.__settings else tag.role(self.__settings["role"])

    def get_next_reserve(self):
        for r in self.data["reserve"]:
            if "called" not in r:
                return r
        return None

    def call_next_reserve(self):
        r = self.get_next_reserve()
        if r is not None:
            r["called"] = True
            self.__sync()
        return r

    def contains_user(self, user: int) -> bool:
        return self.contains_player(user) or self.contains_reserve(user)

    def contains_player(self, user: int) -> bool:
        return any(u["id"] == user for u in self.data["players"])

    def contains_reserve(self, user: int) -> bool:
        return any(u["id"] == user for u in self.data["reserve"])

    def add_player(self, player):
        self.data["players"].append(player)
        self.__sync()
        self.remove_reserve(player["id"])

    def remove_player(self, player_id):
        self.__remove_from_playerlist("players", player_id)
        if not self.full:
            auto = None
            for r in self.data["reserve"]:
                if "auto" in r:
                    auto = r
                    break

            if auto is not None:
                if "auto" in auto:
                    del auto["auto"]
                self.add_player(auto)

    def add_reserve(self, reserve):
        self.data["reserve"].append(reserve)
        self.__sync()
        self.remove_player(reserve["id"])

    def remove_reserve(self, player_id):
        self.__remove_from_playerlist("reserve", player_id)

    def set_auto_join(self, user, auto=True):
        for player in self.data["reserve"]:
            if player["id"] == user:
                if auto:
                    player["auto"] = True
                elif "auto" in player:
                    del player["auto"]
                self.__sync()
                break

    def __remove_from_playerlist(self, playerlist, player_id):
        if playerlist not in self.data:
            return

        player = None

        for x in self.data[playerlist]:
            if x["id"] == player_id:
                player = x
                break

        if player:
            self.data[playerlist].remove(player)
            self.__sync()

    def generate_header_message(self) -> str:
        count = ""
        if self.num_players > 0:
            count = f"**({self.num_players}/{self.size})** "

        role = f"{self.__role}! " if self.__role is not None else ""
        return f"{role}Scrim {f'*{self.name}* ' if self.name is not None else ''}" \
               f"at {self.scrim_time()} {count}" \
               f"started by {tag.user(self.author['id'])}"

    def generate_player_list(self, separator="\n") -> str:
        return separator.join(map(lambda p: p['mention'], self.data["players"]))

    def generate_reserve_list(self, separator="\n") -> str:
        def __map_reserve(reserve: dict):
            if "auto" in reserve and not self.started:
                return f"{reserve['mention']} (auto-join)"
            if "called" in reserve:
                return f"{reserve['mention']} (called)"
            return reserve['mention']

        return separator.join(map(__map_reserve, self.data["reserve"]))

    def generate_start_messages(self) -> tuple[str, Optional[str]]:
        if self.num_players == 0:
            return "Sad moment, nobody signed up! Archiving the thread.", None

        players = self.generate_player_list(separator=' ')
        reserves = self.generate_reserve_list(separator=' ')

        if self.full:
            return f"Scrim starting, get online!\n" \
                   f"{players}", None

        if self.num_players + self.num_reserves >= self.size:
            return f"Scrim starting, get online!\n" \
                   f"{players}\n" \
                   f"Reserves, we might need you!\n" \
                   f"{reserves}", None

        thread_msg = f"Not enough players, feel free to get online and try to get it started anyway!\n" \
                     f"{players}\n"
        channel_msg = None

        if self.num_reserves > 0:
            thread_msg += f"Reserves, feel free to join in.\n" \
                          f"{reserves}"

        shortage = self.size - (self.num_players + self.num_reserves)
        if shortage <= 2:
            role = f"{self.__role}" if self.__role is not None else "Scrimmers"
            channel_msg = f"{role}, you might be able to make this a full scrim.\n" \
                          f"We need at least {shortage} player(s)."

        return thread_msg, channel_msg

    def scrim_time(self, separator=" / "):
        s = self.time.strftime("%H:%M")
        l = tag.time(self.time)
        timezone = "server" if self.timezone is None else self.timezone.zone
        return f"{s} ({timezone}){separator}{l} (your local time)"
