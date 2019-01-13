class Registry():
    PLUGINS = dict()
    APP = None

    def register_get(self, endpoint: str):
        def decorator_register_get(func):
            self.PLUGINS[f'get,{endpoint}'] = {'func': func}
            return func
        return decorator_register_get

    @classmethod
    def set_app(cls, app) -> None:
        cls.APP = app

        for endpoint, func_dict in cls.PLUGINS.items():
            func = func_dict['func']
            func.__defaults__ = (app,)
            func.__kwdefaults__ = {'app': app}

registry = Registry()
