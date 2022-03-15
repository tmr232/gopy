from gopy import *


class Greeter:
    name: str


def Hello(g: Receiver[Greeter]):
    print(f"Hello, {g.name}!")


def Goodbye(g: Receiver[Greeter]):
    print(f"Goodbye, {g.name}.")


class Enum(Const):
    One = iota + 1
    Two
    Three


def main():
    greeter = Greeter(name="Golang")
    defer(lambda: greeter.Goodbye())
    greeter.Hello()

    print(f"{Enum.One=}\n"
          f"{Enum.Two=}\n"
          f"{Enum.Three=}")
