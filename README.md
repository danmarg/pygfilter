# GFilter: Pythonic Gmail Filters

GFilter is a Pythonic eDSL for creating Gmail mail filters, along with a Gmail
API client for automatically parsing and uploading the resultant filters. 

This is best illustrated with an example:

```
$ pip3 install git+https://github.com/danmarg/pygfilter#egg=gfilter
$ cat my_filters.py 
from functools import reduce
from gfilter.dsl import *

# Map of list ID -> label.
lists = {
        "list1@some_list.com": "Lists/List1",
        "list2@lists.somelistorg": "Lists/List2",
    }

rules = (
    # Mailing lists
    [List(a) >= L(b) for a, b in lists.items()] +
    # Mark them all as 'autocleanup', too.
    [reduce(lambda x, y: x|y, [List(x) for x in lists.keys()]) >= L('autocleanup')]
)
$ gfilter personal_filters.py -u
Parsed 3 rules.
```

Note that unless explicitly specified (`--nooverwrite`), gfilter *will*
*overwrite* existing filters!
