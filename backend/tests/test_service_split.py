"""The customer/admin service split must expose exactly the monolith's API.

Also checks the nginx gateway rule (gateway/nginx.conf): every monolith route
must be sent to a service that actually serves it.
"""

import re
from pathlib import Path

import pytest
from fastapi.routing import APIRoute

from app.admin_main import app as admin_app
from app.customer_main import app as customer_app
from app.main import app as monolith_app

NGINX_CONF = Path(__file__).resolve().parents[2] / "gateway" / "nginx.conf"
API_PREFIX = "/api/v1"
SHARED_ROUTES = {
    ("POST", "/api/v1/auth/login"),
    ("POST", "/api/v1/auth/register"),
    ("GET", "/api/v1/me"),
    ("GET", "/api/v1/health"),
}


def _routes(app) -> set[tuple[str, str]]:
    return {
        (method, route.path)
        for route in app.routes
        if isinstance(route, APIRoute) and route.path.startswith(API_PREFIX)
        for method in route.methods
    }


def _admin_location_regex() -> re.Pattern:
    match = re.search(r"location\s+~\s+(\^/api/v1/\S+)\s*\{", NGINX_CONF.read_text())
    assert match, "admin-service regex location not found in gateway/nginx.conf"
    return re.compile(match.group(1))


def test_split_covers_every_monolith_route():
    assert _routes(customer_app) | _routes(admin_app) == _routes(monolith_app)


def test_only_auth_me_and_health_are_on_both_services():
    assert _routes(customer_app) & _routes(admin_app) == SHARED_ROUTES


@pytest.mark.parametrize("method,path", sorted(_routes(monolith_app)))
def test_gateway_routes_to_a_service_that_serves_the_path(method, path):
    sample_path = re.sub(r"\{[^}]+\}", "00000000-0000-0000-0000-000000000000", path)
    target = admin_app if _admin_location_regex().match(sample_path) else customer_app
    assert (method, path) in _routes(target)
