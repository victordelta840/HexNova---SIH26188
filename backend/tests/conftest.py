from tests.auth_helpers import AUTH_HEADERS


def pytest_configure(config) -> None:
    config.auth_headers = AUTH_HEADERS
