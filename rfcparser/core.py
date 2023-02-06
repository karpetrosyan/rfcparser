from datetime import datetime
from pathlib import Path

from lark import Lark, Token

from .exceptions import ParseException, ValidationException
from .object_abstractions import Cookie6265, Uri3986

# Files
RFC6265_DATE = "grammars/rfc6265_date.lark"
RFC6265_SETCOOKIE = "grammars/rfc6265_set_cookie.lark"
RFC1034_DOMAIN = "grammars/rfc1034_domain.lark"
RFC822_DOMAIN = "grammars/rfc822_domain.lark"
RFC3986_URI = "grammars/rfc3986_uri.lark"


def collect_tokens(tree):
    return "".join(token.value for token in tree.children)


class LazyLoadLark:
    def __init__(self, value, **kwargs):
        self.value = value
        self.parser = None
        self.kwargs = kwargs

    def __get__(self, obj, type):
        if self.parser is None:
            path = str(Path(__file__).parent / self.value)
            with open(path) as f:
                self.parser = Lark(f.read(), source_path=path, **self.kwargs)
                del self.kwargs
        return self.parser


class DateParser6265:
    default_start = "cookie_date"
    date_parser = LazyLoadLark(
        RFC6265_DATE, start=["cookie_date", "time", "year", "month", "day_of_month"]
    )

    month_map = {
        "jan": 1,
        "feb": 2,
        "mar": 3,
        "apr": 4,
        "may": 5,
        "jun": 6,
        "jul": 7,
        "aug": 8,
        "sep": 9,
        "oct": 10,
        "nov": 11,
        "dec": 12,
    }

    # rules
    DATE_TOKEN = "date_token"
    TIME = "time"
    YEAR = "year"
    MONTH = "month"
    DAY_OF_MONTH = "day_of_month"

    def can_parse(self, value, start=None):
        try:
            self.date_parser.parse(value, start=start or self.default_start)
            return True
        except Exception:
            return False

    def tree_parse(self, tree):
        found_time = None
        found_day_of_month = None
        found_month = None
        found_year = None
        hour_value = None
        minute_value = None
        second_value = None
        year_value = None
        day_of_month_value = None
        month_value = None

        date_tokens = tree.children[0]
        date_tokens_values = []

        for token in date_tokens.children:
            if (token.data == self.DATE_TOKEN) or ():
                date_tokens_values.append(collect_tokens(token))
        for token in date_tokens_values:
            if (found_time is None) and self.can_parse(token, self.TIME):
                found_time = token
                h, m, s = token.split(":")
                hour_value = int(h)
                minute_value = int(m)
                second_value = int(s)
            elif found_day_of_month is None and self.can_parse(
                token, self.DAY_OF_MONTH
            ):
                found_day_of_month = token
                day_of_month_value = int(token)

            elif found_month is None and self.can_parse(token, self.MONTH):
                found_month = token
                month_value = self.month_map[token.lower()]
            elif found_year is None and self.can_parse(token, self.YEAR):
                found_year = token
                year_value = int(token)

        if 70 <= year_value <= 99:
            year_value += 1900

        elif 0 <= year_value <= 99:
            year_value += 2000

        if not (found_time and found_month and found_year and found_day_of_month):
            missing_attributes = []
            if not found_time:
                missing_attributes.append("time")
            if not found_month:
                missing_attributes.append("month")
            if not found_year:
                missing_attributes.append("year")
            if not found_day_of_month:
                missing_attributes.append("day_of_month")
            raise ValidationException(
                (
                    "One or more attributes aren't being"
                    "passed. Missing attributes : %s" % (missing_attributes,)
                )
            )
        if 1 > day_of_month_value or day_of_month_value > 31:
            raise ValidationException("The month's day must be between [1, 31].")
        if year_value < 1601:
            raise ValidationException("The year value must be greater than 1600.")
        if hour_value > 23:
            raise ValidationException("The hour value cannot be greater than 23.")
        if minute_value > 59:
            raise ValidationException("The minute value cannot be greater than 59.")
        if second_value > 59:
            raise ValidationException("The second value cannot be greater than 59.")

        date = datetime(
            year=year_value,
            day=day_of_month_value,
            month=month_value,
            minute=minute_value,
            hour=hour_value,
            second=second_value,
        )
        return date

    def parse(self, value, start=None):
        try:
            tree = self.date_parser.parse(value, start=start or self.default_start)
            return self.tree_parse(tree)
        except Exception as ex:
            raise ParseException from ex


class SetCookieParser6265:
    default_start = "set_cookie_header"
    set_cookie_parser = LazyLoadLark(RFC6265_SETCOOKIE, start=["set_cookie_header"])

    def tree_parse(self, tree, uri):
        (cookie_name,) = tuple(tree.find_data("cookie_name"))
        (cookie_value,) = tuple(tree.find_data("cookie_value"))

        cookie_name = collect_tokens(cookie_name).strip()
        cookie_value = collect_tokens(cookie_value).strip()

        attrs = {}
        attrs_nodes = tuple(tree.find_data("cookie_av"))

        for attrs_node in attrs_nodes:
            for attr in attrs_node.children:
                if attr.data == "expires_av":
                    cookie_date_parser = DateParser6265()
                    expire_date = cookie_date_parser.tree_parse(
                        attr.children[0].children[0]
                    )
                    attrs["Expires"] = expire_date
                elif attr.data == "path_av":
                    path = collect_tokens(attr.children[0])
                    attrs["Path"] = path
                elif attr.data == "httponly_av":
                    attrs["HttpOnly"] = True
                elif attr.data == "max_age_av":
                    attrs["Max-Age"] = int(collect_tokens(attr))
                elif attr.data == "secure_av":
                    attrs["Secure"] = True
                elif attr.data == "domain_av":
                    attrs["Domain"] = collect_tokens(attr.children[0].children[0])
                elif attr.data == "extension_av":
                    key, value = collect_tokens(attr).split("=")
                    attrs[key] = value
        set_cookie = Cookie6265(
            key=cookie_name, value=cookie_value, attrs=attrs, uri=uri
        )

        return set_cookie

    def parse(self, value, uri, start=None):
        try:
            tree = self.set_cookie_parser.parse(
                value, start=start or self.default_start
            )
            return self.tree_parse(tree, uri)
        except Exception as ex:
            raise ParseException from ex


class DomainParser822:
    default_start = "domain"
    domain_parser = LazyLoadLark(RFC822_DOMAIN, start=["domain"])

    def tree_parse(self, tree):
        sub_domains = []
        for sub_domain in tree.children:
            label = collect_tokens(sub_domain)
            sub_domains.append(label)
        return sub_domains

    def parse(self, value, start=None):
        try:
            tree = self.domain_parser.parse(value, start=start or self.default_start)
            return self.tree_parse(tree)
        except Exception as ex:
            raise ParseException from ex


class DomainParser1034:
    default_start = "domain"
    domain_parser = LazyLoadLark(RFC1034_DOMAIN, start=["domain"])

    def tree_parse(self, tree):
        first_subdomain = tree.children[0]
        subdomains = []

        def subdomain_collector(node):
            start = 0
            if not isinstance(node.children[0], Token):
                start += 1
                subdomain_collector(node.children[0])

            children = ""
            for i in range(start, len(node.children)):
                children += node.children[i].value
            subdomains.append(children)

        subdomain_collector(first_subdomain)
        return subdomains

    def parse(self, value, start=None):
        try:
            tree = self.domain_parser.parse(value, start=start or self.default_start)
            return self.tree_parse(tree)
        except Exception as ex:
            raise ParseException from ex


class UriParser3986:
    default_start = "uri"
    uri_parser = LazyLoadLark(RFC3986_URI, start=["uri", "relative_ref"])

    def tree_parse(self, tree):
        # trees
        (authority,) = tree.find_data("authority")
        (hier_part,) = tree.find_data("hier_part")
        path_tree = hier_part.children[-1]
        try:
            (query_tree,) = tree.find_data("query")
        except ValueError:
            query_tree = None
        try:
            (fragment,) = tree.find_data("fragment")
            fragment = collect_tokens(fragment)
        except ValueError:
            fragment = None

        scheme = collect_tokens(tree.children[0])
        tmp_ip = ""
        ip = None
        port = None
        host = None
        userinfo = None
        path = ""
        query = {}

        query_temp_key_value = ["", ""]
        query_switch = 0

        for child in authority.children:
            if child:
                if child.data == "host":
                    first_child = child.children[0]
                    if first_child.data == "ip_4address":
                        for dec_octet in first_child.children:
                            tmp_ip += collect_tokens(dec_octet) + "."
                        tmp_ip = tmp_ip[:-1]
                    elif first_child.data == "reg_name":
                        host = collect_tokens(first_child).split(".")
                    elif first_child.data == "ip_6address":
                        raise NotImplementedError(
                            "Parsertool does not support ipv6 addresses"
                        )

                elif child.data == "port":
                    port = collect_tokens(child)

                elif child.data == "userinfo":
                    userinfo = collect_tokens(child)

        for child in path_tree.children:
            path += "/" + collect_tokens(child)

        if query_tree:
            for child in query_tree.children:
                if not isinstance(child, Token):
                    query_switch += 1
                    if query_switch == 2:
                        key, value = query_temp_key_value
                        query[key] = value
                        query_temp_key_value = ["", ""]
                        query_switch = 0
                else:
                    query_temp_key_value[query_switch] += child.value
            if query_switch == 1:
                key, value = query_temp_key_value
                query[key] = value

        return Uri3986(
            scheme=scheme,
            ip=tmp_ip or ip,
            port=int(port) if port else None,
            host=host,
            userinfo=userinfo,
            path=path or "/",
            query=query,
            fragment=fragment,
        )

    def parse(self, value, start=None):
        try:
            tree = self.uri_parser.parse(value, start=start or self.default_start)
            return self.tree_parse(tree)
        except Exception as ex:
            raise ParseException from ex
