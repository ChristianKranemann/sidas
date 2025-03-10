from sidas.extensions.resources.databases import SqliteResource


def test_resource() -> None:
    resource = SqliteResource(":memory:")
    assert resource


def test_resource_engine() -> None:
    resource = SqliteResource(":memory:")
    engine = resource.get_engine()
    assert engine


def test_resource_connection() -> None:
    resource = SqliteResource(":memory:")
    with resource.get_connection() as connect:
        assert connect
