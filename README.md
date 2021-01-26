# pyretree
 Hook simplified regular expressions (see example for syntax) to functions and extract keywords from the results. Can support massive numbers of hooks with no noticeable performance penalty.
 
Example use:
 ```python
from pyretree import pyretree

# See syntax below
music_players = '(spotify|winamp|itunes)'
app_words = '(app|application|program)'

intentions = pyretree.RegexCollection()

# Syntax: Use <> to extract keywords from text: <positional_variable> <named_variable="">
# () is a group, | is a logical OR, and ? is a existential quantifier, just like in normal regular expressions.
# {} is Python string formatting. Use this with your own collections of commonly used words to cut down on repetition.
@intentions.add('play <song>')
@intentions.add(f'play <song> (with|using|on)( {app_words})? <app={music_players}>')
def play_song_with(song, app=None):
    if app is None:
        print(f'Playing "{song.title()}"')
    else:
        print(f'Asking {app.title()} to play "{song.title()}"')

# (as many other functions as you like)

# Build the RegexCollection
intentions.prepare()


# Using the built RegexCollection
intentions.match('play fake arms by foreign fields')
# > Playing "Fake Arms By Foreign Fields"

intentions.match('play fake arms by foreign fields with spotify')
# > Asking Spotify to play "Fake Arms By Foreign Fields"
```
