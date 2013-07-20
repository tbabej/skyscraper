from bs4 import BeautifulSoup
from selenium import webdriver
from datetime import datetime


def removeNonAscii(string):
    return "".join(i for i in string if ord(i) < 128)

months = {
             1: 'leden',
             2: 'unor',
             3: 'brezen',
             4: 'duben',
             5: 'kveten',
             6: 'cerven',
             7: 'cervenec',
             8: 'srpen',
             9: 'zari',
             10: 'rijen',
             11: 'listopad',
             12: 'prosinec'
         }

browser = webdriver.Firefox()


class Flight(object):

    def __init__(self, dep, arr, price, date, dep_time, arr_time):
        self.departure = dep
        self.arrival = arr
        self.price = price
        self.date = date
        self.departure_time = dep_time
        self.arrival_time = arr_time

    def __str__(self):
        str_template = '{price}, {date}: From {dep} ({dep_time}) '\
                       'to {arr} ({arr_time})'
        description = str_template.format(dep=self.departure,
                                          arr=self.arrival,
                                          price=self.price,
                                          date=self.date,
                                          dep_time=self.departure_time,
                                          arr_time=self.arrival_time)
        return description


class SkyscannerMonthView(object):

    url_tmpl = 'http://www.skyscanner.cz/lety/'\
               '{dep}/{arr}/{mon}-{year}/{mon}-{year}'

    classes = [" selectable item",
               "weekend selectable item",
               "weekend last selectable item",
              ]

    def scrape(self, departure_airport, arrival_airport, year, month):
        url = self.url_tmpl.format(dep=departure_airport,
                                   arr=arrival_airport,
                                   year=str(year),
                                   mon=months.get(month))

        browser.get(url)

        source = browser.page_source

        page = BeautifulSoup(source)
        departure_calendar = page.find_all(id='outboundDates_calendar')[0]
        arrival_calendar = page.find_all(id='inboundDates_calendar')[0]

        departure_entries = []
        arrival_entries = []
        departures = []
        arrivals = []

        date = datetime(year, month, 1)

        for cls in self.classes:
            departure_entries += departure_calendar.find_all(class_=cls)
            arrival_entries += arrival_calendar.find_all(class_=cls)

        for (entries, flights) in ((departure_entries, departures),
                                   (arrival_entries, arrivals)):
            for entry in entries:
                flight = self.create_flight_from_entry(entry,
                                                       date,
                                                       departure_airport,
                                                       arrival_airport)
                flights.append(flight)

    def create_flight_from_entry(cls, string, date, departure_airport,
                                 arrival_airport):
        # Does it have price?
        if string.find_all(class_="noprices"):
            return None

        # Parse out price
        price_raw = string.find_all(class_="price")[0].contents[0]
        price = int(removeNonAscii(price_raw))  # 2998

        # Parse out day of the month
        day_raw = string.find_all(class_="day")[0].contents[0]
        day = int(removeNonAscii(day_raw))  # 2

        date.replace(day=day)

        desc_raw = string.attrs['tooltip2']  # 'BRQ-PMI 19:30-09:25'

        # Does it have arrival/departure time defined?
        if len(desc_raw.split(' ')) > 1:
            # BRQ-PMI 11:05-20:35
            times = desc_raw.split(' ')[1].split('-')
            dep_time = datetime(times[0], "%H:%M").replace(day=date.day,
                                                           month=date.month,
                                                           year=date.year)

        else:
            dep_time = '?'
            arr_time = '?'

        flight = cls(departure_airport,
                     arrival_airport,
                     price,
                     date,
                     dep_time,
                     arr_time)

        return flight



