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

# Mailing lists
[List(a) >= L(b) for a, b in lists.items()]
# Mark them all as 'autocleanup', too.
[reduce(lambda x, y: x|y, [List(x) for x in lists.keys()]) >= L('autocleanup')]

$ gfilter personal_filters.py -u
Parsed 3 rules.
```

Note that unless explicitly specified (`--nooverwrite`), gfilter *will*
*overwrite* existing filters!

# Language Reference

The GFilter eDSL consists of rules comprised of one or more conditions and a
single action, joined with the `>=` operator. For example:
```
From('spammer@spamdomain.com' >= SkipInbox()
```

Conditions (see [here](https://support.google.com/mail/answer/7190) for more):

* `Has`: Gmail `has:` operator
* `List`: Gmail `list:` operator
* `To`: Gmail `to:` operator
* `Cc`: Gmail `cc:` operator
* `From`: Gmail `from:` operator
* `Subject`: Gmail `subject:` operator
* `DeliveredTo`: Gmail `deliveredto:` operator
* `HasAttachment`: Equivalent to `has:attachment`
* `Is`: Gmail `is:` operator
* `Exact`: Matches mail with exactly this string

Conditions can be combined with the following logical operators:

* `+`: Logical and
* `|`: Logical or
* `~`: Logical not
* `Any([list])`: Matches if any of the conditions in the list are true
* `All([list])`: Matches if all of the conditions in the list are true

Actions can be one of the following:

* `Star()`: Add a star
* `SkipInbox()`: Skip the inbox
* `L(label)`: Add `label` as a label
* `~L(label)`: Remove `label` as a label
