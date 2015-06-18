from __future__ import unicode_literals

import weakref

from .data import LATEST_YEAR, data, index
from ._compat import unicode_compatible, unicode_type


@unicode_compatible
class Division(object):
    """The administrative division."""

    _identity_map = dict(
        (year, weakref.WeakValueDictionary()) for year in data)

    def __init__(self, code, name, year=None):
        self.code = unicode_type(code)
        self.name = unicode_type(name)
        self.year = year

    def __repr__(self):
        if self.year is None:
            return 'gb2260.get(%r)' % self.code
        else:
            return 'gb2260.get(%r, %r)' % (self.code, self.year)

    def __str__(self):
        name = 'GB2260' if self.year is None else 'GB2260-%d' % self.year
        humanize_name = '/'.join(x.name for x in self.stack())
        return '<%s %s %s>' % (name, self.code, humanize_name)

    def __hash__(self):
        return hash((self.__class__, self.code, self.year))

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.code == other.code and self.year == other.year

    @classmethod
    def get(cls, code, year=None):
        """Gets an administrative division by its code.

        :param code: The division code.
        :param year: The year of revision.
        :returns: A :class:`gb2260.Division` object.
        """
        key = int(code)
        if year and year not in data:
            raise ValueError('year must be in %r' % list(data))

        cache = cls._identity_map[year]
        store = data[year]

        if key in cache:
            return cache[key]
        if key in store:
            instance = cls(code, store[key], year)
            cache[key] = instance
            return instance

        raise ValueError('%r is not valid division code' % code)

    @classmethod
    def search(cls, code):
        """Searches administrative division by its code in all revision.

        :param code: The division code.
        :returns: A :class:`gb2260.Division` object or ``None``.
        """
        # sorts from latest to oldest, and ``None`` means latest
        key = int(code)
        pairs = sorted(
            data.items(), reverse=True,
            key=lambda pair: make_year_key(pair[0]))
        for year, store in pairs:
            if key in store:
                return cls.get(key, year=year)

    @classmethod
    def query(cls, name, higher_code=0, is_prefecture=False):
        """Query administrative division by its name in all revision.

        :param name: the division name or its alias or its used name.
        :param higher_code: the division code at the higher division.
        :param is_prefecture: specify the division level
                    when prefecture/county has the same alias.
        :returns: A :class:`gb2260.Division` object or ``None``.
        """

        if isinstance(name, bytes):
            name = name.decode('utf-8')

        if name not in index:
            return None

        limit = 10000 if higher_code % 10000 == 0 else 100
        for code, year in index[name]:
            if not higher_code or higher_code/limit == code/limit:
                if is_prefecture and code % 100 != 0:
                    continue
                return cls.get(code, year)
        return None

    @property
    def province(self):
        return self.get(self.code[:2] + '0000', self.year)

    @property
    def is_province(self):
        return self.province == self

    @property
    def prefecture(self):
        if self.is_province:
            return
        return self.get(self.code[:4] + '00', self.year)

    @property
    def is_prefecture(self):
        return self.prefecture == self

    @property
    def county(self):
        if self.is_province or self.is_prefecture:
            return
        return self

    @property
    def is_county(self):
        return self.county is not None

    def stack(self):
        yield self.province
        if self.is_prefecture or self.is_county:
            yield self.prefecture
        if self.is_county:
            yield self


def make_year_key(year):
    """A key generator for sorting years."""
    if year is None:
        return (LATEST_YEAR, 12)
    year = str(year)
    if len(year) == 4:
        return (int(year), 12)
    if len(year) == 6:
        return (int(year[:4]), int(year[4:]))
    raise ValueError('invalid year %s' % year)
