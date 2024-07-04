
class ContextAwareToolMixin:
    def __init__(self, **kwargs):
        context = kwargs.pop("context", None)
        super().__init__(**kwargs)
        self.context = context or {}
