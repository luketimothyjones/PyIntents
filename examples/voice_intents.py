import os
import sys
sys.path.append(os.path.abspath('..'))

import subprocess

import phrases
from pyretree import pyretree

intentions = pyretree.RegexCollection()
music_players = "(spotify|winamp|itunes)"

# ----
@intentions.add("open <app>")
def open_app(app):
    print(f"Opening {app.title()}")
    subprocess.run(app)


@intentions.add(f"open <file> {phrases.use_app} <app>")
def open_file_with(file, app):
    print(f'Asking {app.title()} to open "{file}"')


@intentions.add("play")
def play():
    print("Playing music")
    

@intentions.add("play <song>")
@intentions.add(f"play <song> {phrases.use_app} <app={music_players}>")
def play_song_with(song, app=None):
    if app is None:
        print(f'Playing "{song.title()}"')
    else:
        print(f'Asking {app.title()} to play "{song.title()}"')


@intentions.add(f"play video <video>")
@intentions.add(f"play video <video> {phrases.use_app} <player>")
def video(video, player="youtube"):
    print(f"Asking {player.title()} to play {video.title()}")
    
# ----
intentions.prepare()
