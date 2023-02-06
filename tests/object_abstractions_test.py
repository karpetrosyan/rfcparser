from datetime import datetime, timedelta

import pytest

from rfcparser.core import SetCookieParser6265, UriParser3986
from rfcparser.object_abstractions import Cookie6265, Uri3986, path_matches


class TestUri3986:
    @pytest.mark.parametrize(
        "value, expected",
        [
            (
                "http://example.com",
                Uri3986(
                    scheme="http",
                    ip=None,
                    port=None,
                    host=["example", "com"],
                    userinfo=None,
                    path=None,
                    query={},
                    fragment=None,
                ),
            ),
            (
                "https://127.0.0.1/path?name=test#fr",
                Uri3986(
                    scheme="https",
                    ip="127.0.0.1",
                    port=None,
                    host=None,
                    userinfo=None,
                    path="/path",
                    query={"name": "test"},
                    fragment="fr",
                ),
            ),
            (
                "https://testdata@127.0.0.1:1010/path?name=test#fr",
                Uri3986(
                    scheme="https",
                    ip="127.0.0.1",
                    port=1010,
                    host=None,
                    userinfo="testdata",
                    path="/path",
                    query={"name": "test"},
                    fragment="fr",
                ),
            ),
        ],
    )
    def test_parsing(self, value, expected):
        parsed = UriParser3986().parse(value)

        assert parsed.scheme == expected.scheme
        assert parsed.ip == expected.ip
        assert parsed.port == expected.port
        assert parsed.host == expected.host
        assert parsed.userinfo == expected.userinfo
        assert parsed.path == expected.path
        assert parsed.query == expected.query
        assert parsed.fragment == expected.fragment
        assert parsed == expected

    @pytest.mark.parametrize(
        "value, newvalue, expected",
        [
            (
                UriParser3986().parse("https://google.com/path?name=test"),
                "/new/path",
                "https://google.com/new/path?name=test",
            ),
            (
                UriParser3986().parse("https://google.com/path?name=test"),
                "new/path",
                "https://google.com/new/path?name=test",
            ),
            (
                UriParser3986().parse("https://google.com/path?name=test"),
                "",
                "https://google.com/?name=test",
            ),
        ],
    )
    def test_update_path(self, value, newvalue, expected):
        value.path = newvalue
        assert str(value) == expected

    @pytest.mark.parametrize(
        "value, newvalue, expected",
        [
            (
                UriParser3986().parse("https://google.com/path?name=test"),
                "//test.com/path?name=test",
                "https://test.com/path?name=test",
            ),
            (
                UriParser3986().parse("https://google.com/path?name=test"),
                "/newpath#asd",
                "https://google.com/newpath#asd",
            ),
        ],
    )
    def test_update_relative_path(self, value, newvalue, expected):
        try:
            UriParser3986().uri_parser.parse(
                "//test.com/path?name=test", start="relative_ref"
            )
        except Exception:
            raise Exception("Invalid relative_ref value") from None
        new_value = value.updated_relative_ref(newvalue)
        assert new_value == expected


class TestSetCookie6265:
    @pytest.mark.parametrize(
        "value, uri, expected",
        [
            (
                "key=value",
                UriParser3986().parse("https://example.com"),
                dict(
                    key="key",
                    value="value",
                    persistent_flag=False,
                    domain="",
                    host_only_flage=False,
                    secure_only_flage=False,
                    http_only_flag=False,
                ),
            )
        ],
    )
    def test_cookie_parse(self, value, uri, expected):
        cookie = SetCookieParser6265().parse(value, uri)
        assert cookie.key == expected["key"]
        assert cookie.value == expected["value"]
        assert cookie.persistent_flag == expected["persistent_flag"]
        assert cookie.domain == expected["domain"]
        assert cookie.host_only_flag == expected["host_only_flag"]
        assert cookie.secure_only_flag == expected["secure_only_flag"]
        assert cookie.http_only_flag == expected["http_only_flag"]


@pytest.mark.parametrize(
    "request_path, cookie_path, expected",
    [
        ("/label1/label2", "/label1", True),
        ("/label1/label2", "/label1/", True),
        ("/label1/label2", "/label/", False),
        ("/label1/label2", "/", True),
        ("/label1", "/", True),
        ("/", "/", True),
        ("/a", "/", True),
    ],
)
def test_path_matches(request_path, cookie_path, expected):
    assert path_matches(request_path, cookie_path) == expected


def test_expiry_time():
    uri = UriParser3986().parse("https://example.com")
    expiry_time = datetime.now() + timedelta(minutes=123123)
    attrs = {"Max-Age": 20, "HttpOnly": True, "Expires": expiry_time}
    cookie = Cookie6265(key="test", value="test", uri=uri, attrs=attrs)
    assert cookie.expiry_time != expiry_time
