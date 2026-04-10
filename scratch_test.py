import copy

class BaseContext:
    def __init__(self, dict_=None):
        self.dicts = [dict_]
        self.foo = "bar"

    def __copy__(self):
        duplicate = type(self).__new__(type(self))
        duplicate.__dict__.update(self.__dict__)
        duplicate.dicts = self.dicts[:]
        return duplicate

class Context(BaseContext):
    def __init__(self):
        super().__init__()
        self.render_context = "render"

    def __copy__(self):
        duplicate = super().__copy__()
        duplicate.render_context = copy.copy(self.render_context)
        return duplicate

c = Context()
c2 = copy.copy(c)
print(type(c2))
print(c2.foo)
print(c2.dicts)
print(c2.render_context)
