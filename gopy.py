import importlib.util
import sys
import inspect
import types
from functools import wraps
from typing import Any, Callable, NamedTuple
from const import Const

KEYWORDS = ["Receiver", "gostruct", "gofunction", "defer", "Const"]
__all__ = ["magic"] + KEYWORDS

IMPORT_FLAG = "__magically_imported__"


class Receiver:
    def __init__(self, receiver: Any) -> None:
        self.receiver = receiver

    def __class_getitem__(cls, item):
        # To ensure we don't miss any method, we'll add every existing method
        # before the one being defined now.
        add_all_methods(get_calling_module())

        return cls(item)


class Namespace(NamedTuple):
    locals: dict
    globals: dict


def get_calling_namespace() -> Namespace:
    for frameinfo in inspect.stack():
        if frameinfo.filename == __file__:
            continue

        return Namespace(locals=frameinfo.frame.f_locals, globals=frameinfo.frame.f_globals)


def gostruct(cls: type):
    init_args = ", ".join(f"{name}=None" for name in cls.__annotations__.keys())
    initialization = "\n".join((f"    if {name} is None: self.{name} = {typ.__name__}()\n"
                                f"    else: self.{name} = {name}")
                               for name, typ in cls.__annotations__.items())
    init_source = (f"def __init__(self, *, {init_args})->None:\n"
                   f"{initialization}")

    ns_locals, ns_globals = get_calling_namespace()
    ns_locals.update(get_calling_module().__dict__)
    exec(init_source, ns_globals, ns_locals)
    init = (ns_locals["__init__"])
    setattr(cls, "__init__", init)
    return cls


_dtor_stack = []


def get_dtor_stack():
    return _dtor_stack


class DtorScope:
    def __init__(self):
        self.stack = []
        get_dtor_stack().append(self)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        get_dtor_stack().pop()

        while self.stack:
            self.stack.pop()()

    def push(self, deferred):
        self.stack.append(deferred)


def push_dtor(cm):
    return get_dtor_stack()[-1].push(cm)


def gofunction(f):
    @wraps(f)
    def _wrapper(*args, **kwargs):
        with DtorScope():
            return f(*args, **kwargs)

    return _wrapper


def defer(callback: Callable[[], Any]) -> None:
    push_dtor(callback)


def get_calling_module():
    for frameinfo in inspect.stack():
        if frameinfo.filename == __file__:
            continue

        module = inspect.getmodule(frameinfo.frame)
        if module:
            return module


def get_method_receiver(method: types.FunctionType) -> type | None:
    signature = inspect.signature(method)
    receiver_param = next(iter(signature.parameters.values()), None)
    if not receiver_param:
        return None

    if isinstance(receiver_param.annotation, Receiver):
        return receiver_param.annotation.receiver


def is_method(obj) -> bool:
    if not inspect.isfunction(obj):
        return False

    return get_method_receiver(obj) is not None


g_seen_methods = set()


def add_method(method) -> bool:
    if method in g_seen_methods:
        return False

    receiver = get_method_receiver(method)
    if receiver is None:
        return False

    setattr(receiver, method.__name__, method)

    # If the name is `String`, we also implement the `Stringer` interface!
    if method.__name__ == "String":
        setattr(receiver, "__repr__", method)

    return True


def add_all_methods(calling_module) -> None:
    for name, value in inspect.getmembers(calling_module, inspect.isfunction):
        add_method(value)


def inject_keywords(module):
    for name in KEYWORDS:
        setattr(module, name, globals()[name])


def decorate_module_functions(module):
    for name, value in inspect.getmembers(module):
        if not inspect.isroutine(value):
            continue

        # Only convert functions that were defined in the importing file.
        # We don't want to convert library imports and the likes of those.
        if inspect.getmodule(value) != module:
            continue

        setattr(module, name, gofunction(value))


def decorate_module_classes(module):
    for name, value in inspect.getmembers(module):
        if not inspect.isclass(value):
            continue

        if issubclass(value, Const):
            continue

        # Only convert functions that were defined in the importing file.
        # We don't want to convert library imports and the likes of those.
        if inspect.getmodule(value) != module:
            continue

        setattr(module, name, gostruct(value))


def import_by_path(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    setattr(module, IMPORT_FLAG, True)
    spec.loader.exec_module(module)
    return module


def _magic():
    calling_module = get_calling_module()

    inject_keywords(calling_module)

    name = calling_module.__name__
    path = calling_module.__file__
    if hasattr(calling_module, IMPORT_FLAG):
        return

    imported_module = import_by_path(name, path)

    decorate_module_functions(imported_module)
    decorate_module_classes(imported_module)
    add_all_methods(imported_module)

    if imported_module.__name__ == "__main__":
        sys.exit(imported_module.main())


def __getattr__(name):
    if name != "magic":
        raise AttributeError()

    _magic()
