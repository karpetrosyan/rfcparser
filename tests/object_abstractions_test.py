from datetime import datetime, timedelta

import pytest

from rfcparser.core import DateParser6265, SetCookieParser6265, UriParser3986
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
                    path="",
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
                    domain="example.com",
                    host_only_flag=True,
                    secure_only_flag=False,
                    http_only_flag=False,
                ),
            ),
            (
                (
                    "GPS=1; Domain=youtube.com; Expires=Tue, "
                    "07-Feb-2023 13:20:04 GMT; Path=/; Secure; HttpOnly"
                ),
                UriParser3986().parse("https://youtube.com"),
                dict(
                    key="GPS",
                    value="1",
                    persistent_flag=True,
                    domain="youtube.com",
                    host_only_flag=False,
                    secure_only_flag=True,
                    http_only_flag=True,
                ),
            ),
            (
                (
                    "ASD=1; Expires=Tue, "
                    "07-Feb-2023 13:20:04 GMT; Domain=youtube.com; "
                    "Secure; HttpOnly; Path=/"
                ),
                UriParser3986().parse("https://youtube.com"),
                dict(
                    key="ASD",
                    value="1",
                    persistent_flag=True,
                    domain="youtube.com",
                    host_only_flag=False,
                    secure_only_flag=True,
                    http_only_flag=True,
                ),
            ),
            (
                ("test=test1; Domain=youtube.com; " "Secure; Path=/"),
                UriParser3986().parse("https://youtube.com"),
                dict(
                    key="test",
                    value="test1",
                    persistent_flag=False,
                    domain="youtube.com",
                    host_only_flag=False,
                    secure_only_flag=True,
                    http_only_flag=False,
                ),
            ),
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


class TestDateParser6265:
    @pytest.mark.parametrize(
        "value, expected",
        (
            (
                "Tue, 07-Feb-2023 13:20:04 GMT",
                datetime(day=7, month=2, year=2023, hour=13, minute=20, second=4),
            ),
            (
                "Tue, 25-Aug-2003 17:45:04 GMT",
                datetime(day=25, month=8, year=2003, hour=17, minute=45, second=4),
            ),
        ),
    )
    def test_date_parser(self, value, expected):
        assert DateParser6265().parse(value) == expected


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
