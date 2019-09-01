from gfilter.dsl import *

# Map of list ID -> label.
lists = {
        "dailydave@lists.immunitysec.com": "Daily Dave"
        }

rules = [List(a) >= Label(b) for a, b in lists.items()]
