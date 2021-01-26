import os
import sys
sys.path.append(os.path.abspath('..'))

from pyretree import pyretree

t = pyretree.RegexTree()
t.add('re1', lambda: 1)
t.add('re2', lambda: 2)
t.add('re3', lambda: 3)
t.add('re4', lambda: 4)
t.add('re5', lambda: 5)

print(t)
print(repr(t))

t.build_tree()

print(t)
print(repr(t))
