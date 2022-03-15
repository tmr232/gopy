"""
Design Note:

This is how we activate the go code.

We also add the package-directive to name our package.
"""
from go import *
package("main")

"""
Design Note:

When importing the module, we query all the variables annotated in it.
For each variable of a matching type (str, bytes) we get the source line.
Then we check the line above for the directive.
Since we check for an entire line, this is valid. Icky, but valid.
Naturally, this does _not_ work for .pyc files, as they don't store
the comments.
"""
#go:embed some-file
stuff: bytes

"""
Design Note:

All classes are like dataclasses.
"""
class Thing:
    x: int
    y: dict
    Public:int
    private:int

"""
Design Note:

When `Received.__class_getitem__` is called, we inspect the calling
scope to preserve all previous functions with the same name.
This allows us to have overloads without any decoration!

Additionally, this means we can directly link the method to the object.
That said, we still need a global pass to link the _last_ method of every
name.
"""
def Print(t:Receiver[Thing])->None:
    print(t.x, t.y)



def main():
    print("Hello, World!")