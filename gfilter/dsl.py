import functools
from typing import List

RULES = []

## Conditions

class __Cond__:
    query = ''

    def __str__(self):
        return 'Cond("' + self.query + '")'

    # Operator overloading for easy combinations.
    def __invert__(self):
        return Not(self)
    def __and__(self, cond):  # TODO: type hint for cond
        return And(self, cond)
    def __or__(self, cond):
        return Or(self, cond)
    # Use >= to construct rules.
    def __ge__(self, actions):  # TODO: type annotation for action
        try:
            iterator = iter(actions)
            return Rule(self, actions)
        except TypeError:
            return Rule(self, [actions])

class Cond(__Cond__):
    '''Matches all mail matching the given query.'''
    def __init__(self, query: str):
        self.query = query

class Has(Cond):
    '''Matches with the 'has' syntax.'''
    def __init__(self, has: str):
        super().__init__('has:' + has)

class List(Cond):
    '''Matches all mail to a given list.'''
    def __init__(self, list: str):
        super().__init__('list:' + list)

class To(Cond):
    '''Matches all mail To a given address.'''
    def __init__(self, to: str):
        super().__init__('to:' + to)

class Cc(Cond):
    '''Matches all mail CC'ing a given address.'''
    def __init__(self, cc: str):
        super().__init__('cc:' + cc)

class From(Cond):
    '''Matches all mail From a given address.'''
    def __init__(self, frm: str):
        super().__init__('from:' + frm)

class Subject(Cond):
    '''Matches all mail with a given Subject.'''
    def __init__(self, subject: str):
        super().__init__('subject:(' + subject + ')')

class DeliveredTo(Cond):
    '''Matches all mail with a given Delivered-To.'''
    def __init__(self, deliveredto: str):
        super().__init__('deliveredto:' + deliveredto)

class Is(Cond):
    '''Matches all mail with a given "is" type.'''
    def __init__(self, isstr: str):
        super().__init__('is:' + isstsr)

class HasAttachment(Cond):
    '''Matches all mail with an attachment.'''
    def __init__(self):
        super().__init__('has:attachment')

class Larger(Cond):
    '''Matches all mail larger than a given size.'''
    def __init__(self, size: str):
        super().__init__('larger:' + size)

class Smaller(Cond):
    '''Matches all mail smaller than a given size.'''
    def __init__(self, size: str):
        super().__init__('smaller:' + size)

class Exact(Cond):
    '''Matches all mail with an exact match.'''
    def __init__(self, exact: str):
        super().__init__('\'' + exact + '\'')

### Match combinations

class And(__Cond__):
    '''And requires a match of two conditions.'''
    def __init__(self, left: __Cond__, right: __Cond__):
        self.query = '(' + left.query + ') AND (' + right.query + ')'

class Or(__Cond__):
    '''Or requires a match of one of two conditions.'''
    def __init__(self, left: __Cond__, right: __Cond__):
        self.query = '(' + left.query + ') OR (' + right.query + ')'

class Not(__Cond__):
    '''Not inverts a match of a condition.'''
    def __init__(self, cond: __Cond__):
        self.query = '-(' + cond.query + ')'

class Any(__Cond__):
    '''Any matches if any of the conditions match.'''
    def __init__(self, conds):  # TODO: add list type hint
        self.query = functools.reduce(Or, conds).query

class All(__Cond__):
    '''All matches if all of the conditions match.'''
    def __init__(self, conds):  # TODO: add list type hint
        self.query = functools.reduce(And, conds).query

## Actions

class __Action__:
    add_label = None
    remove_label = None
    def __init__(self, add: str, remove: str):
        self.add_label = add
        self.remove_label = remove
    def __str__(self):
        s = ''
        if self.add_label:
            s += 'L("' + self.add_label + '")'
        if self.remove_label:
            s += '~L("' + self.remove_label + '")'
        return s

# Special labels: add a star, skip the inbox, or trash.
Star = __Action__('STARRED', None)
SkipInbox = __Action__(None, 'INBOX')
Trash = __Action__('TRASH', None)

class L(__Action__):
    def __init__(self, label: str):
        super().__init__(label, None)

    def __invert__(self):
        '''Invert (~) of a label will remove that label.'''
        return __Action__(self.remove_label, self.add_label)

## Rules
class Rule:
    cond = None
    actions = []
    def __init__(self, cond: __Cond__, actions):  # TODO: add list type hint for
                                                  # actions
        self.cond = cond
        self.actions = actions
        RULES.append(self)

    def __str__(self):
        return '(' + str(self.cond) + ') >= ' + '[' + ', '.join(
                [str(a) for a in self.actions]) + ']'
