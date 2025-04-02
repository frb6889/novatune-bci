import json
def load_song(song_name):

    file_path = f"data/songs/{song_name}.json"
    
    try:
        with open(file_path, "r") as f:
            song_sections = json.load(f)
        return song_sections
    except FileNotFoundError:
        print(f"没有找到曲子文件: {file_path}")
        return None