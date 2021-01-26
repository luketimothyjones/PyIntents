import os
import sys
sys.path.append(os.path.abspath('..'))

import pprint
import random
import string

from pyretree import pyretree
import phrases


def add_intentions(intentions):
    # ----
    @intentions.add("play")
    def play():
        return "Playing music"
        
    @intentions.add("open <app>")
    def open_app(app):
        return f"Opening {app.title()}"


    @intentions.add(f"open <file> (with|using) <app>")
    def open_file_with(file, app):
        return f'Asking {app.title()} to open "{file}"'
        

    @intentions.add("play <song>")
    @intentions.add(f"play <song> with <app=(zune|play music)>")
    def play_song_with(song, app=None):
        if app is None:
            return f'Playing "{song.title()}"'
        else:
            return f'Asking {app.title()} to play "{song.title()}"'
            

    @intentions.add(f"play video <video>")
    @intentions.add(f"play video <video> with <player>")
    def video(video, player="youtube"):
        return f'Asking {player.title()} to play "{video.title()}"'

        
    @intentions.add("turn on the light <time>")
    def light_time(time):
        return f"The light will turn on {time}"
    
    @intentions.add("turn on the light at <time>")
    def light_time(time):
        return f"The light will turn on at {time}"    
        
    @intentions.add("turn on the light")
    @intentions.add("turn on the light now")
    @intentions.add("turn on the light pronto")
    def light():
        return "Turning on the light"

        
# ==============================================


# ========
def generate_random_intentions(func_count, dec_count=8):        
    intents_data = ''
    tests_data = ''

    def get_word():
        characters = string.ascii_uppercase + string.digits
        return ''.join(random.SystemRandom().choice(characters) for _ in range(random.randint(2, 7)))

    for c in range(func_count):
        words = ' '.join((get_word() for _ in range(random.randint(1, 5))))
        
        intents_data += f'@intentions.add("{words} <param>")\n'
        tests_data   += f'    results.append(intentions.match("{words} {get_word()}")[0])\n'
        
        for i in range(dec_count):
            decorator_diff = get_word()
            intents_data += f'@intentions.add("{words} {decorator_diff} <param>")\n'
            tests_data   += f'    results.append(intentions.match("{words} {decorator_diff} {get_word()}")[0])\n'

        intents_data += f'def intent_{c}(param): return param\n'

    # Load and fill templates
    with open('templates/stress_tests.template', 'r') as sfile:
        stests_out = sfile.read().format(tests=tests_data, func_count=func_count, dec_count=dec_count)
        
    with open('templates/stress_intents.template', 'r') as ifile:
        istress_out = ifile.read().format(intents=intents_data)
         
    # Write filled templates
    with open('stress_tester.py', 'w') as tests_file:
        print(stests_out, file=tests_file)
        
    with open('stress_intents.py', 'w') as intents_file:
        print(istress_out, file=intents_file)

        
def get_intentions():
    intentions = pyretree.RegexCollection()
    add_intentions(intentions)

    intentions.prepare()
    
    return intentions
