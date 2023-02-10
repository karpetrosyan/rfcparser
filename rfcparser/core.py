import ipaddress
import re
import warnings
from datetime import datetime, timedelta
from pathlib import Path

from lark import Lark, Token

from .exceptions import ParseException
from .object_abstractions import Cookie6265, Uri3986, default_path

warnings.filterwarnings("ignore")

# Files
RFC6265_DATE = "grammars/rfc6265_date.lark"
RFC1034_DOMAIN = "grammars/rfc1034_domain.lark"
RFC822_DOMAIN = "grammars/rfc822_domain.lark"
RFC3986_URI = "grammars/rfc3986_uri.lark"


def collect_tokens_recursive(tree):
    if isinstance(tree.children[0], Token):
        return [collect_tokens(tree)]
    else:
        return collect_tokens_recursive(tree.children[0]) + [
            "".join(token.value for token in tree.children[1:])
        ]


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
    non_delimiter_ranges = (
        (0x00, 0x08),
        (0x0A, 0x1F),
        (48, 58),
        (97, 123),
        (0x7F, 0xFF),
        (65, 91),
    )
    non_delimiter = {
        ":",
    } | set(chr(i) for start, end in non_delimiter_ranges for i in range(start, end))

    hms_time_regex = re.compile(r"(\d{1,2}:){2}\d{1,2}")
    year_regex = re.compile(r"\d{2,4}")
    day_of_month_regex = re.compile(r"\d{1,2}")
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

    def validate(
        self,
        year_value,
        minute_value,
        second_value,
        day_of_month_value,
        month_value,
        hour_value,
        found_month,
        found_year,
        found_time,
    ):
        if 70 <= year_value <= 99:
            year_value += 1900
        if 0 <= year_value <= 69:
            year_value += 2000

        if (
            not (all((day_of_month_value, found_month, found_year, found_time)))
            and (1 <= day_of_month_value <= 31)
            and (year_value < 1601)
            and (hour_value > 23)
            and (minute_value > 59)
            and (second_value > 59)
        ):
            raise ValueError("Invalid date")
        return datetime(
            year=year_value,
            month=month_value,
            day=day_of_month_value,
            hour=hour_value,
            minute=minute_value,
            second=second_value,
        )

    def parse(self, date):
        date_tokens = []
        start = None

        for ind, char in enumerate(date):
            if char not in self.non_delimiter:
                if start is not None:
                    date_tokens.append(date[start:ind])
                    start = None
            else:
                if start is None:
                    start = ind
        if start is not None:
            date_tokens.append(date[start:])

        found_time = None
        found_day_of_month = None
        found_month = None
        found_year = None

        hour_value = None
        minute_value = None
        second_value = None
        day_of_month_value = None
        month_value = None
        year_value = None

        for token in date_tokens:
            if not found_time and self.hms_time_regex.match(token):
                found_time = True
                hour_value, minute_value, second_value = token.split(":")
                hour_value = int(hour_value)
                minute_value = int(minute_value)
                second_value = int(second_value)

            elif not found_month and token.lower() in self.month_map:
                found_month = True
                month_value = int(self.month_map[token.lower()])

            elif not found_day_of_month and self.day_of_month_regex.match(token):
                found_day_of_month = True
                day_of_month_value = int(token)

            elif not found_year and self.year_regex.match(token):
                found_year = True
                year_value = int(token)

        try:
            return self.validate(
                year_value=year_value,
                month_value=month_value,
                second_value=second_value,
                minute_value=minute_value,
                hour_value=hour_value,
                day_of_month_value=day_of_month_value,
                found_month=found_month,
                found_year=found_year,
                found_time=found_time,
            )
        except Exception:
            return None


class SetCookieParser6265:
    def validate(self, attrs, uri):
        cleaned_attrs = {}

        for attribute_name, attribute_value in attrs.items():
            if attribute_name.lower() == "expires":
                try:
                    expiry_time = DateParser6265().parse(attribute_value)
                except Exception:
                    continue
                cleaned_attrs["Expires"] = expiry_time

            elif attribute_name.lower() == "max-age":
                brk = False
                if not (attribute_value[0].isdigit() or attribute_value[0] == "="):
                    continue

                for char in attribute_value:
                    if not char.isdigit():
                        brk = True
                        continue
                if brk:
                    continue
                delta_seconds = int(attribute_value)
                if delta_seconds <= 0:
                    expiry_time = datetime.now()
                else:
                    expiry_time = datetime.now() + timedelta(seconds=delta_seconds)
                cleaned_attrs["Max-Age"] = expiry_time

            elif attribute_name.lower() == "domain":
                if not attribute_value:
                    continue

                if attribute_value[0] == ".":
                    cookie_domain = attribute_value[1:]
                else:
                    cookie_domain = attribute_value
                cookie_domain = cookie_domain.lower()
                cleaned_attrs["Domain"] = cookie_domain

            elif attribute_name.lower() == "path":
                if (not attribute_value) or (attribute_value[0] != "/"):
                    cookie_path = default_path(uri)
                else:
                    cookie_path = attribute_value
                cleaned_attrs["Path"] = cookie_path

            elif attribute_name.lower() == "secure":
                cleaned_attrs["Secure"] = ""
            elif attribute_name.lower() == "httponly":
                cleaned_attrs["HttpOnly"] = ""

        return cleaned_attrs

    def parse(self, value, uri, start=None):
        if ";" in value:
            name_value_pair = value.split(";")[0]
            unparsed_attributes = value[value.find(";") :]
        else:
            name_value_pair = value
            unparsed_attributes = ""
        eq_ind = name_value_pair.find("=")
        if eq_ind == -1:
            return None
        name = name_value_pair[:eq_ind].strip()
        value = name_value_pair[eq_ind + 1 :].strip()
        attrs = {}

        if not name:
            raise None

        while unparsed_attributes:
            unparsed_attributes = unparsed_attributes[1:]
            sep_ind = unparsed_attributes.find(";")
            if sep_ind != -1:
                cookie_av = unparsed_attributes[:sep_ind]
            else:
                cookie_av = unparsed_attributes
            eq_ind = cookie_av.find("=")
            if eq_ind != -1:
                attribute_name = cookie_av[:eq_ind]
                attribute_value = cookie_av[eq_ind + 1 :]
            else:
                attribute_name = cookie_av
                attribute_value = ""
            attribute_name = attribute_name.strip()
            attribute_value = attribute_value.strip()
            attrs[attribute_name] = attribute_value
            unparsed_attributes = unparsed_attributes[sep_ind:]

        cleaned_attrs = self.validate(attrs, uri)
        return Cookie6265(key=name, value=value, uri=uri, attrs=cleaned_attrs)


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
    uri_parsing_regex = re.compile(
        r"^(([^:/?#]+):)?(//([^/?#]*))?([^?#]*)(\?([^#]*))?(#(.*))?"
    )

    def parse(self, value):
        match = self.uri_parsing_regex.search(value)
        if not match:
            return None

        query_dict = {}
        scheme = match.group(2)
        authority = match.group(4)
        path = match.group(5)
        query = match.group(7)
        fragment = match.group(9)

        sep_ind = authority.find("@")
        if sep_ind != -1:
            userinfo = authority[:sep_ind]
            authority = authority[sep_ind + 1 :]
        else:
            userinfo = None

        sep_ind = authority.find(":")
        if sep_ind != -1:
            port = int(authority[sep_ind + 1 :])
            authority = authority[:sep_ind]
        else:
            port = None

        host = authority
        try:
            ipaddress.ip_address(host)
            ip = host
            host = None
        except Exception:
            ip = None

        if query:
            for key_value in query.split("&"):
                key, value = key_value.split("=")
                query_dict[key] = value

        if host:
            host = host.split(".")

        return Uri3986(
            scheme=scheme,
            ip=ip,
            port=int(port) if port else None,
            host=host,
            userinfo=userinfo,
            path=path,
            query=query_dict,
            fragment=fragment,
        )
