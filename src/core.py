from lark import Lark
from pathlib import Path
from datetime import datetime

from exceptions import ValidationException, ParseException


class LazyLoadLark:

    def __init__(self, value, **kwargs):
        self.value = value
        self.parser = None
        self.kwargs = kwargs

    def __get__(self, obj, type):
        if self.parser is None:
            path = str(Path(__file__).parent / self.value)
            with open(path) as f:
                print('loading')
                self.parser = Lark(f.read(), **self.kwargs)
                del self.kwargs
        return self.parser


class DateParseManager:
    default_start = 'cookie_date'
    date_parser = LazyLoadLark('rfc6265_date.lark', start=["cookie_date", "time",
                                                           "year", "month", "day_of_month"])

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
        "dec": 12
    }

    def can_parse(self, value, start=None):
        try:
            self.date_parser.parse(value, start=start or self.default_start)
            return True
        except Exception as e:
            return False

    def date_parse(self, value, start=None):
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

        try:
            tree = self.date_parser.parse(value, start=start or self.default_start)
        except Exception as ex:
            raise ParseException from ex
        date_tokens = tree.children[0]
        date_tokens_values = []
        for token in date_tokens.children:
            if token.data == 'date_token':
                date_tokens_values.append(''.join(non_delimiter.value for
                                                  non_delimiter in token.children))
        for token in date_tokens_values:
            if (found_time is None) and self.can_parse(token, 'time'):
                found_time = token
                h, m, s = token.split(':')
                hour_value = int(h)
                minute_value = int(m)
                second_value = int(s)
            elif found_day_of_month is None and self.can_parse(token, 'day_of_month'):
                found_day_of_month = token
                day_of_month_value = int(token)

            elif found_month is None and self.can_parse(token, "month"):
                found_month = token
                month_value = self.month_map[token.lower()]
            elif found_year is None and self.can_parse(token, "year"):
                found_year = token
                year_value = int(token)

        if 70 <= year_value <= 99:
            year_value += 1900

        elif 0 <= year_value <= 99:
            year_value += 2000

        if not (found_time and found_month and found_year and found_day_of_month):
            missing_attributes = []
            if not found_time: missing_attributes.append('time')
            if not found_month: missing_attributes.append('month')
            if not found_year: missing_attributes.append('year')
            if not found_day_of_month: missing_attributes.append('day_of_month')
            raise ValidationException(
                ("One or more attributes aren't being"
                 "passed. Missing attributes : %s" % (missing_attributes,)))
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

        date = datetime(year=year_value, day=day_of_month_value,
                        month=month_value, minute=minute_value,
                        hour=hour_value, second=second_value)
        return date
