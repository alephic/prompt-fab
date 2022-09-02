from typing import Any, Union, Optional, Mapping
import re

__all__ = [
    "Template",
    "Fixed",
    "Pattern",
    "Integer",
    "Append",
    "Repeat",
    "NumberedList",
    "Affix",
    "Suffix",
    "Prefix",
    "Record",
    "Option",
    "SENTENCE",
    "EOL",
    "SPACE",
    "YES_NO",
    "NUM"
]

class StringPos:
    """
    Helper class to allow position in a string to be passed by reference.
    """
    def __init__(self, s, pos=0):
        self.s = s
        self.pos = pos
    def advance(self, n):
        self.pos += n

class Template:
    """
    Template base class.
    Templates can convert data to string representations via .fill,
    or parse data from string representations via .match

    Custom Template subclasses should override ._match, not .match
    """
    def _match(self, sp: StringPos):
        raise NotImplementedError()
    def match(self, s: str, pos=0):
        return self._match(StringPos(s, pos=pos))
    def fill(self, *args):
        raise NotImplementedError()

class Fixed(Template):
    """
    Template that always surfaces a fixed string.
    """
    def __init__(self, default, accepted_pattern=None):
        self.default = default
        accepted_pattern = default if accepted_pattern is None else accepted_pattern
        self.accepted_pattern = re.compile(accepted_pattern)
    def fill(self, *args):
        return self.default
    def _match(self, sp: StringPos):
        m = self.accepted_pattern.match(sp.s, pos=sp.pos)
        if m is None:
            return None
        else:
            sp.advance(len(m.group(0)))
            return m.group(0)

def str_to_fixed(str_or_template: Union[str, Template]):
    if isinstance(str_or_template, Template):
        return str_or_template
    elif isinstance(str_or_template, str):
        return Fixed(str_or_template)
    else:
        raise ValueError('Expected string or template')

NOTHING = Fixed('')

class Pattern(Template):
    """
    Template that surfaces strings. When parsing via .match,
    a Pattern instance will only consume strings that match its
    regular expression (specified by the pattern argument)
    """
    def __init__(self, pattern: str):
        self.pattern = re.compile(pattern)
        self.group_idx = 0 if self.pattern.groups == 0 else 1
    def _match(self, sp: StringPos):
        m = self.pattern.match(sp.s, pos=sp.pos)
        if m is None:
            return None
        else:
            sp.advance(len(m.group(0)))
            return m.group(self.group_idx)
    def fill(self, s):
        if s is None:
            return ''
        return s

class Integer(Pattern):
    """
    Template that maps integers to strings.
    """
    def __init__(self):
        super().__init__(r'-?[0-9]+')
    def _match(self, sp: StringPos):
        revert_pos = sp.pos
        s = super()._match(sp)
        try:
            i = int(s, base=10)
        except (ValueError, TypeError) as e:
            sp.pos = revert_pos
            return None
        return i
    def fill(self, i):
        if i is None:
            return ''
        return super().fill(str(i))

class Append(Template):
    """
    Template that maps a fixed-length sequence to a string by applying a series
    of item_templates to the corresponding entries in the sequence.
    """
    def __init__(self, *item_templates: Union[str, Template]):
        self.item_templates = tuple(map(str_to_fixed, item_templates))
    def _match(self, sp: StringPos):
        matches = []
        for item_template in self.item_templates:
            if (m := item_template._match(sp)) is None:
                return None
            matches.append(m)
        return tuple(matches)
    def fill(self, items):
        if items is None:
            return ''
        return ''.join(item_template.fill(item) for item_template, item in zip(self.item_templates, items))

class Repeat(Template):
    """
    Template that maps a sequence to a string by applying item_template to each
    element of the sequence, separating elements with the provided delimiter.
    """
    def __init__(self, item_template: Template, delimiter: Union[str, Fixed], trailing_delimiter=False):
        self.item_template = item_template
        self.delimiter = str_to_fixed(delimiter)
        self.trailing_delimiter = trailing_delimiter
    def _match(self, sp: StringPos):
        vals = []
        i_revert = sp.pos
        last_dm = None
        while (m := self.item_template._match(sp)) is not None:
            vals.append(m)
            i_revert = sp.pos
            if (last_dm := self.delimiter._match(sp)) is None:
                break
        if (last_dm is not None) and not self.trailing_delimiter:
            sp.pos = i_revert
        return vals

    def fill(self, values):
        if values is None:
            return ''
        d = self.delimiter.fill()
        filled = d.join(
            self.item_template.fill(v) for v in values
        )
        return filled+d if self.trailing_delimiter else filled

class NumberedList(Repeat):
    """
    Template that maps a sequence to a numbered list. This template accepts
    a label_template that should map integers to strings,
    and an item_template which should surface the actual list entries.
    Example:
    >>> t = NumberedList(Suffix(NUM, '. '), SENTENCE, EOL)
    >>> print(t.fill(['This is Sentence One.', 'Copy that, Sentence One - Sentence Two here.']))
    1. This is Sentence One.
    2. Copy that, Sentence One.
    """
    def __init__(self, label_template: Template, item_template: Template, delimiter: Union[str, Fixed], trailing_delimiter=False, start_idx=1):
        super().__init__(Append(label_template, item_template), delimiter, trailing_delimiter=trailing_delimiter)
        self.start_idx = start_idx
    
    def _match(self, sp):
        sm = super()._match(sp)
        return None if sm is None else [pair[1] for pair in sm]
    
    def fill(self, values):
        if values is None:
            return ''
        return super().fill(zip(map(str, range(self.start_idx, len(values)+self.start_idx)), values))

class Affix(Template):
    """
    Template that adds fixed decoration to either (or both) sides of a given content template.
    """
    def __init__(self, prefix: Union[str, Fixed], content: Template, suffix: Optional[Union[str, Fixed]] = None):
        self.prefix = str_to_fixed(prefix)
        self.content = content
        self.suffix = None if suffix is None else str_to_fixed(suffix)
    def _match(self, sp: StringPos):
        pm = self.prefix._match(sp)
        if pm is None:
            return None
        cm = self.content._match(sp)
        if cm is None:
            return None
        if self.suffix is not None:
            self.suffix._match(sp)
        return cm
    def fill(self, c):
        filled = self.prefix.fill()+self.content.fill(c)
        if self.suffix is not None and c is not None:
            filled += self.suffix.fill()
        return filled

class Suffix(Affix):
    def __init__(self, content: Template, suffix: Union[str, Fixed]):
        super().__init__(NOTHING, content, suffix=suffix)

Prefix = Affix

class Record(Template):
    """
    Template that maps the named fields of a record to a sequence of concatenated templates.
    Example:
    >>> t = Record(
          a=Affix(NUM, ' '),
          b=NUM
        )
    >>> print(t.fill({'a': 1, 'b': 2}))
    1 2
    >>> t.match('1 2')
    {'a': 1, 'b': 2}
    """
    def __init__(self, **fields: Mapping[str, Union[str, Template]]):
        self.fields = {name: str_to_fixed(str_or_template) for name, str_or_template in fields.items()}
    def _match(self, sp: StringPos):
        rec = {}
        for field_name, field_template in self.fields.items():
            m = field_template._match(sp)
            if m is not None:
                rec[field_name] = m
        return rec
    def fill(self, rec):
        if rec is None:
            return ''
        return ''.join(f.fill(rec.get(f_name)) for f_name, f in self.fields.items() if f_name in rec)

class Option(Template):
    """
    Template that maps between a set of values and arbitrary strings corresponding to each value.
    """
    def __init__(self, value_templates: Mapping[Any, Union[str, Fixed]]):
        self.value_templates = {value: str_to_fixed(str_or_fixed) for value, str_or_fixed in value_templates.items()}
    def _match(self, sp: StringPos):
        for val, val_template in self.value_templates.items():
            m = val_template._match(sp)
            if m is not None:
                return val
        return None
    def fill(self, val):
        if val is None:
            return ''
        return self.value_templates[val].fill()

# Any string that (optionally) ends in a sentence-ending punctuation mark
# and doesn't run longer than a single line
SENTENCE = Pattern(r'[^\n\.\?\!]+[\.\?\!]?')
EOL = Fixed('\n')
SPACE = Fixed(' ', accepted_pattern=r' +')
YES_NO = Option({False: 'No', True: 'Yes'})
NUM = Integer()