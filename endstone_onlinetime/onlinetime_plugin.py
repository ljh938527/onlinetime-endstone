import json

from endstone import Player, ColorFormat
from endstone.event import PlayerJoinEvent, event_handler
from endstone.command import Command, CommandSender
from endstone.plugin import Plugin

version = '0.0.1'

class OnlineTime(Plugin):
    
    api_version = '0.5'
    
    def __init__(self):
        super().__init__()
        self.time_data_file = 'plugins/onlinetime/onlinetime.json'
        self.time_data = self.load_time_data()
        self.top_list = []
        self.top = ""
    
    def on_load(self):
        if not self.data_folder.exists():
            self.data_folder.mkdir()
            
    def load_time_data(self):
        try:
            with open(self.time_data_file, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            if not self.data_folder.exists():
                self.data_folder.mkdir()
            with open(self.time_data_file, "w") as f:
                json.dump({}, f)
            return {}
    
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
            sender.send_message("Your online time is " + ColorFormat.GREEN + str(self.get_time(sender)) + " minutes" + ColorFormat.WHITE +".")
        if command.name == "onlinetimetop":
            sender.send_message(ColorFormat.GREEN + "Online Time Top\n" + ColorFormat.WHITE + self.top)
        return True
    
    def add_time(self, pl: Player):
        player_xuid = str(pl.xuid)
        self.time_data[player_xuid]["time"] += 1
    
    def handle_time_data(self):
        tlist = [(player["name"], player["time"]) for player in self.time_data.values()]
        self.top_list = sorted(tlist, key=lambda x:x[1], reverse = True)
    
    def interval(self):
        with open(self.time_data_file, "w") as f:
            json.dump(self.time_data, f)
        for player in self.server.online_players:
            self.add_time(player)
        self.handle_time_data()
        top_strings = [f"{name} : {time}" for name,time in self.top_list]
        self.top = "\n".join(top_strings)
    
    def on_enable(self):
        self.register_events(self)
        self.server.scheduler.run_task(self, self.interval, delay=0, period=1200)
