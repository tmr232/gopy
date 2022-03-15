import itertools
import operator
from typing import Any


class Iota:
    """Go's iota"""
    lhs: Any
    op: Any
    rhs: Any

    def __init__(self, lhs, op, rhs):
        self.lhs = lhs
        self.op = op
        self.rhs = rhs

    @classmethod
    def make_iota(cls):
        return cls(lhs=itertools.count(), op=operator.add, rhs=0)

    def __add__(self, other):
        return Iota(self, operator.add, other)

    def __radd__(self, other):
        return Iota(other, operator.add, self)

    def __sub__(self, other):
        return Iota(self, operator.sub, other)

    def __rsub__(self, other):
        return Iota(other, operator.sub, self)

    def __mul__(self, other):
        return Iota(self, operator.mul, other)

    def __rmul__(self, other):
        return Iota(other, operator.mul, self)

    def __truediv__(self, other):
        return Iota(self, operator.truediv, other)

    def __rtruediv__(self, other):
        return Iota(other, operator.truediv, self)

    def __floordiv__(self, other):
        return Iota(self, operator.floordiv, other)

    def __rfloordiv__(self, other):
        return Iota(other, operator.floordiv, self)

    def __pow__(self, other, modulo=None):
        return Iota(self, operator.pow, other)

    def __rpow__(self, other):
        return Iota(other, operator.pow, self)

    def __lshift__(self, other):
        return Iota(self, operator.lshift, other)

    def __rlshift__(self, other):
        return Iota(other, operator.lshift, self)

    def __rshift__(self, other):
        return Iota(self, operator.rshift, other)

    def __rrshift__(self, other):
        return Iota(other, operator.rshift, self)

    def __calculate__(self):
        lhs = self.lhs
        if isinstance(lhs, type(self)):
            lhs = lhs.__calculate__()
        elif isinstance(lhs, itertools.count):
            lhs = next(lhs)
        rhs = self.rhs
        if isinstance(rhs, type(self)):
            rhs = rhs.__calculate__()
        return self.op(lhs, rhs)


class ConstNamespace(dict):
    """Class namespace for const generation & iota

    See https://docs.python.org/3/reference/datamodel.html#preparing-the-class-namespace
    and https://snarky.ca/unravelling-pythons-classes/ for more info.
    """

    def __init__(self):
        super().__init__()
        self.formula = None

    def __setitem__(self, key, value):
        if isinstance(value, Iota):
            self.formula = value
            super().__setitem__(key, value.__calculate__())
        else:
            super().__setitem__(key, value)

    def __getitem__(self, item):
        try:
            super().__getitem__(item)
        except KeyError:
            if item == "__name__":
                raise
            if item == "iota":
                return Iota.make_iota()
            value = self.formula.__calculate__()
            self[item] = value
            return value


class ConstMeta(type):
    @classmethod
    def __prepare__(metacls, name, bases):
        # Return our custom namespace object
        return ConstNamespace()

    def __new__(cls, name, bases, classdict):
        # Convert the custom object to a regular dict, to avoid unwanted shenanigans.
        return type.__new__(cls, name, bases, dict(classdict))


class Const(metaclass=ConstMeta): pass


class Flags(Const):
    A = 1 << iota
    B
    C


def main():
    assert Flags.A == 1
    assert Flags.B == 2
    assert Flags.C == 4


if __name__ == '__main__':
    main()
