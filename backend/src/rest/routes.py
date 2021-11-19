from .endpoints import ExampleApi


def initialize_routes(api):
    api.add_resource(ExampleApi, '/')
