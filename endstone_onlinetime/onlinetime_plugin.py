import json
import threading
import os

from endstone import Player, ColorFormat
from endstone.event import PlayerJoinEvent, event_handler
from endstone.command import Command, CommandSender
from endstone.scoreboard import DisplaySlot, Criteria
from endstone.plugin import Plugin

version = '0.0.3'

class OnlineTime(Plugin):
    
    api_version = '0.5'
    
    def __init__(self):
        super().__init__()
        self.time_data_file = 'plugins/onlinetime/onlinetime.json'
        self.time_data = self.load_time_data()
        self.config_file = 'plugins/onlinetime/config.json'
        self.configs = self.load_config()
        self.lang = self.load_language()
        self.top_list = []
        self.top = ""
            
    def load_time_data(self):
        try:
            with open(self.time_data_file, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            os.makedirs(os.path.dirname(self.time_data_file), exist_ok=True)
            with open(self.time_data_file, "w") as f:
                json.dump({}, f)
            return {}
    
    def load_config(self):
        try:
            with open(self.config_file, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            config = {"onlinetime_belowname_enable":1,"lang":"en_US"}
            with open(self.config_file, "w") as f:
                json.dump(config, f)
            return config
    
    def load_language(self):
        try:
            with open("plugins/onlinetime/langs/" + self.configs["lang"] + ".json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            if not os.path.exists("plugins/onlinetime/langs/"):
                os.makedirs("plugins/onlinetime/langs/")
            en_US = {"cmd_onlinetime":"Your online time is ","minutes":" minutes","cmd_onlinetimetop":"Online Time Top\n","onlinetime":"{}Online {}Time"}
            zh_CN = {"cmd_onlinetime":"你的在线时长为 ","minutes":" 分钟","cmd_onlinetimetop":"在线时长排行榜\n","onlinetime":"{}在线{}时长"}
            langs = {"en_US":en_US,"zh_CN":zh_CN}
            for lang in langs:
                with open("plugins/onlinetime/langs/" + lang + ".json", "w") as f:
                    json.dump(langs[lang], f)
            return langs[self.configs["lang"]]
    
    @event_handler()
    def check_time(self, event: PlayerJoinEvent):
        player = event.player
        player_name = player.name
        player_xuid = str(player.xuid)
        player_data = self.time_data.get(player_xuid)
        if not player_data:
            self.time_data.update({player_xuid: {"name": player_name, "time": 0}})
    
    def get_time(self, pl: Player):
        player_xuid = str(pl.xuid)
        minutes = self.time_data[player_xuid]["time"]
        return minutes
    
    commands = {
        "onlinetime": {
            "description": "See your online time",
            "usages": ["/onlinetime"],
            "permissions": ["onlinetime_plugin.command.onlinetimetop"],
        },
        "onlinetimetop": {
            "description": "See the online time top of all players",
            "usages": ["/onlinetimetop"],
            "permissions": ["onlinetime_plugin.command.onlinetime"],
        }
    }
    permissions = {
        "onlinetime_plugin.command.onlinetime": {
            "description": "Allow users to use the /onlinetime command.",
            "default": True, 
        },
        "onlinetime_plugin.command.onlinetimetop": {
            "description": "Allow users to use the /onlinetimetop command.",
            "default": True, 
        }
    }
    
    def on_command(self, sender: CommandSender, command: Command, args: list[str]) -> bool:
        if command.name == "onlinetime":
            sender.send_message(self.lang["cmd_onlinetime"] + ColorFormat.GREEN + str(self.get_time(sender)) + self.lang["minutes"])
        if command.name == "onlinetimetop":
            sender.send_message(ColorFormat.GREEN + self.lang["cmd_onlinetimetop"] + ColorFormat.WHITE + self.top)
        return True
    
    def add_time(self, pl: Player):
        player_xuid = str(pl.xuid)
        self.time_data[player_xuid]["time"] += 1
    
    def handle_time_data(self):
        tlist = [(player["name"], player["time"]) for player in self.time_data.values()]
        self.top_list = sorted(tlist, key=lambda x:x[1], reverse = True)
    
    def interval(self):
        for player in self.server.online_players:
            self.add_time(player)
        with open(self.time_data_file, "w") as f:
            json.dump(self.time_data, f)
        self.handle_time_data()
        top_strings = [f"{name} : {time}" for name,time in self.top_list]
        self.top = "\n".join(top_strings)
    
    def on_enable(self):
        self.register_events(self)
        self.server.scheduler.run_task(self, self.interval, delay=0, period=1200)
        if self.configs["onlinetime_belowname_enable"]:
            onlinetime_objective = self.server.scoreboard.get_objective("onlinetime")
            if not onlinetime_objective:
                onlinetime_objective = self.server.scoreboard.add_objective(
                    name="onlinetime",
                    criteria=Criteria.Type.DUMMY,
                    display_name=self.lang["onlinetime"].format(ColorFormat.GREEN, ColorFormat.YELLOW)
                )
            self.onlinetime_objective = onlinetime_objective
            self.onlinetime_objective.set_display(DisplaySlot.BELOW_NAME)
            self.server.scheduler.run_task(self, self.update_belowname, delay=0, period=1200)
    
    def update_belowname(self):
        threading.Thread(target=self.update_belowname_thread).start()

    def update_belowname_thread(self):
        if len(self.server.online_players) == 0:
            return
        for online_player in self.server.online_players:
            player_xuid = str(online_player.xuid)
            self.onlinetime_objective.get_score(online_player).value = self.time_data[player_xuid]["time"]
