from dateutil import parser


def HolidayList():
    # hardcoded until Holiday table is built and utilized
    HList = {
            parser.parse('2023-01-02'),
            parser.parse('2023-01-16'),
            parser.parse('2023-02-20'),
            parser.parse('2023-05-29'),
            parser.parse('2023-06-19'),
            parser.parse('2023-07-04'),
            parser.parse('2023-09-04'),
            parser.parse('2023-11-23'),
            parser.parse('2023-11-24'),
            parser.parse('2023-12-25'),
            parser.parse('2023-12-26'),
            parser.parse('2024-01-01'),
    }

    return HList

