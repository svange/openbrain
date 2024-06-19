
class ContextAwareToolMixin:
    def __init__(self, **kwargs):
        initial_context = kwargs.pop("initial_context", None)
        super().__init__(**kwargs)
        self.initial_context = initial_context or {}
