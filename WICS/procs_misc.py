from cMenu.utils import calvindate
from django.http import HttpRequest
from typing import List


def HolidayList(req:HttpRequest, includePast:bool = True) -> List:
    # hardcoded until Holiday table is built and utilized
    HList = [
        calvindate('2023-01-02').as_datetime(),
        calvindate('2023-01-16').as_datetime(),
        calvindate('2023-02-20').as_datetime(),
        calvindate('2023-05-29').as_datetime(),
        calvindate('2023-06-19').as_datetime(),
        calvindate('2023-07-04').as_datetime(),
        calvindate('2023-09-04').as_datetime(),
        calvindate('2023-11-23').as_datetime(),
        calvindate('2023-11-24').as_datetime(),
        calvindate('2023-12-25').as_datetime(),
        calvindate('2023-12-26').as_datetime(),
        calvindate('2024-01-01').as_datetime(),
    ]
    return HList

