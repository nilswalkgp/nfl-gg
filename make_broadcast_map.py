import json
import nfl_data_py as nfl # type: ignore

year = 2025

schedules = nfl.import_schedules([year])

broadcast_map = {}
for (game_id) in schedules['game_id']:
    broadcast_map[game_id] = "CBS1"

f = open("new_broadcast_map.json", "w")
f.write(json.dumps(broadcast_map, indent=4))
f.close()