#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

# http://www.datypic.com/sc/xsd/t-xsd_dateTime.html
# http://www.datypic.com/sc/xsd/t-xsd_duration.html

import re
from datetime import datetime, timedelta, timezone

from dateutil import tz


def fmt_as_xml_datetime(dt: datetime):
    s = dt.strftime("%Y-%m-%dT%H:%M:%S.%f%z")
    fmtstring = s[:23]
    if dt.tzinfo is not None:
        fmtstring += s[26:29] + ":" + s[29:]
    else:
        fmtstring += "Z"
    return fmtstring


def parse_xml_datetime(s: str,
                       weak: bool = False):
    pattern = r"""
        ^
        (?P<year>\d{4})
        -
        (?P<month>\d{2})
        -
        (?P<day>\d{2})
        T
        (?P<hours>\d{2})
        :
        (?P<minutes>\d{2})
        :
        (?P<seconds>\d{2})
        (\.
            (?P<millis>\d{1,3})
        )?
        (
            (?P<zulu>Z)
            |
            (
                (?P<sign>[-+])
                (?P<tz_h>\d{2})
                :
                (?P<tz_m>\d{2})
            )
        )?
        $
    """

    weak_pattern = r"""
            ^
            (?P<year>\d{4})
            -
            (?P<month>\d{1,2})
            -
            (?P<day>\d{1,2})
            T
            (?P<hours>\d{1,2})
            :
            (?P<minutes>\d{1,2})
            :
            (?P<seconds>\d{1,2})
            (\.
                (?P<millis>\d{1,3})
            )?
            (
                (?P<zulu>Z)
                |
                (
                    (?P<sign>[-+])
                    (?P<tz_h>\d{1,2})
                    :
                    (?P<tz_m>\d{2})
                )
            )?
            $
        """

    p = re.compile(pattern if not weak else weak_pattern, re.VERBOSE)
    q = p.search(s)
    if q is None:
        raise SyntaxError("The passed string is incorrectly formatted")
    year = int(q.group("year"))
    month = int(q.group("month"))
    day = int(q.group("day"))
    hour = int(q.group("hours"))
    minute = int(q.group("minutes"))
    second = int(q.group("seconds"))
    micro = 0 if q.group("millis") is None else int(q.group("millis")) * 1000
    z = q.group("zulu")
    tz_sign = q.group("sign")
    tz_hour = None if q.group("tz_h") is None else int(q.group("tz_h"))
    tz_minute = None if q.group("tz_m") is None else int(q.group("tz_m"))

    zone = None
    if z is not None:
        zone = timezone.utc
    elif tz_sign == "+":
        zone = timezone(timedelta(hours=tz_hour,
                                  minutes=tz_minute))
    elif tz_sign == "-":
        zone = timezone(-timedelta(hours=tz_hour,
                                   minutes=tz_minute))

    return datetime(year, month, day, hour, minute, second, micro, zone)


def fmt_as_xml_duration(dr: timedelta):
    (Y, D) = divmod(dr.days, 365)
    (M, D) = divmod(D, 31)
    (h, s) = divmod(dr.seconds, 3600)
    (m, s) = divmod(s, 60)
    return "P%dY%dM%dDT%sH%sM%sS" % (Y, M, D, h, m, s)


def parse_xml_duration(s: str):
    pattern = r"""
        ^
        P
        (?!$)
        ((?P<years>\d+)Y)?
        ((?P<months>\d+)M)?
        ((?P<days>\d+)D)?
        (
            T
            (?!$)
            ((?P<hours>\d+)H)?
            ((?P<minutes>\d+)M)?
            ((?P<seconds>\d+)
                (?P<millis>\.\d+)?
            S)?
        )?
        $
    """
    p = re.compile(pattern, re.VERBOSE)
    q = p.search(s)
    if q is None:
        raise SyntaxError("The passed string is incorrectly formatted")

    years = int(q.group("years")) if q.group("years") is not None else 0
    months = int(q.group("months")) if q.group("months") is not None else 0
    days = int(q.group("days")) if q.group("days") is not None else 0
    hours = int(q.group("hours")) if q.group("hours") is not None else 0
    minutes = int(q.group("minutes")) if q.group("minutes") is not None else 0
    seconds = int(q.group("seconds")) if q.group("seconds") is not None else 0
    millis = int(float(q.group("millis")) * 1000) if q.group("millis") is not None else 0

    return timedelta(days=365 * years + 31 * months + days,
                     seconds=hours * 3600 + minutes * 60 + seconds,
                     milliseconds=millis)


if __name__ == "__main__":
    a = datetime.now(tz.gettz("CET"))
    print(fmt_as_xml_datetime(a))
    print(a.__class__)

    td = timedelta(500, 4000)
    print(fmt_as_xml_duration(td))

    print(parse_xml_datetime("2004-04-12T13:20:00Z"))
    parse_xml_duration("P2Y6M5DT12H35M30S")
    parse_xml_duration("P1DT2H")
    parse_xml_duration("P20M")
    parse_xml_duration("PT20M")
    parse_xml_duration("P0Y20M0D")
    parse_xml_duration("P0Y")
    parse_xml_duration("P60D")
    parse_xml_duration("PT1M30.5S")
