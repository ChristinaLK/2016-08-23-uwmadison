#!/usr/bin/env python

'''Check that index.html is valid and print out warnings and errors
when the header is malformed.  See the docstrings on the checking
functions for a summary of the checks.
'''

from __future__ import print_function
import sys
import os
import re
import logging
import yaml
from collections import Counter

try:  # Hack to make codebase compatible with python 2 and 3
    our_basestring = basestring
except NameError:
    our_basestring = str

__version__ = '0.6'


# basic logging configuration
logger = logging.getLogger(__name__)
verbosity = logging.INFO  # severity of at least INFO will emerge
logger.setLevel(verbosity)

# create console handler and set level to debug
console_handler = logging.StreamHandler()
console_handler.setLevel(verbosity)

formatter = logging.Formatter('%(levelname)s: %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


# TODO: these regexp patterns need comments inside
EMAIL_PATTERN = r'[^@]+@[^@]+\.[^@]+'
HUMANTIME_PATTERN = r'((0?\d|1[0-1]):[0-5]\d(am|pm)(-|to)(0?\d|1[0-1]):[0-5]\d(am|pm))|((0?\d|1\d|2[0-3]):[0-5]\d(-|to)(0?\d|1\d|2[0-3]):[0-5]\d)'
EVENTBRITE_PATTERN = r'\d{9,10}'
URL_PATTERN = r'https?://.+'

DEFAULT_CONTACT_EMAIL = 'admin@software-carpentry.org'

USAGE = 'Usage: "python check.py" or "python check.py path/to/index.html"\n'

COUNTRIES = [
    'Abkhazia', 'Afghanistan', 'Aland', 'Albania', 'Algeria',
    'American-Samoa', 'Andorra', 'Angola', 'Anguilla',
    'Antarctica', 'Antigua-and-Barbuda', 'Argentina', 'Armenia',
    'Aruba', 'Australia', 'Austria', 'Azerbaijan', 'Bahamas',
    'Bahrain', 'Bangladesh', 'Barbados', 'Basque-Country',
    'Belarus', 'Belgium', 'Belize', 'Benin', 'Bermuda', 'Bhutan',
    'Bolivia', 'Bosnia-and-Herzegovina', 'Botswana', 'Brazil',
    'British-Antarctic-Territory', 'British-Virgin-Islands',
    'Brunei', 'Bulgaria', 'Burkina-Faso', 'Burundi', 'Cambodia',
    'Cameroon', 'Canada', 'Canary-Islands', 'Cape-Verde',
    'Cayman-Islands', 'Central-African-Republic', 'Chad',
    'Chile', 'China', 'Christmas-Island',
    'Cocos-Keeling-Islands', 'Colombia', 'Commonwealth',
    'Comoros', 'Cook-Islands', 'Costa-Rica', 'Cote-dIvoire',
    'Croatia', 'Cuba', 'Curacao', 'Cyprus', 'Czech-Republic',
    'Democratic-Republic-of-the-Congo', 'Denmark', 'Djibouti',
    'Dominica', 'Dominican-Republic', 'East-Timor', 'Ecuador',
    'Egypt', 'El-Salvador', 'England', 'Equatorial-Guinea',
    'Eritrea', 'Estonia', 'Ethiopia', 'European-Union',
    'Falkland-Islands', 'Faroes', 'Fiji', 'Finland', 'France',
    'French-Polynesia', 'French-Southern-Territories', 'Gabon',
    'Gambia', 'Georgia', 'Germany', 'Ghana', 'Gibraltar',
    'GoSquared', 'Greece', 'Greenland', 'Grenada', 'Guam',
    'Guatemala', 'Guernsey', 'Guinea-Bissau', 'Guinea', 'Guyana',
    'Haiti', 'Honduras', 'Hong-Kong', 'Hungary', 'Iceland',
    'India', 'Indonesia', 'Iran', 'Iraq', 'Ireland',
    'Isle-of-Man', 'Israel', 'Italy', 'Jamaica', 'Japan',
    'Jersey', 'Jordan', 'Kazakhstan', 'Kenya', 'Kiribati',
    'Kosovo', 'Kuwait', 'Kyrgyzstan', 'Laos', 'Latvia',
    'Lebanon', 'Lesotho', 'Liberia', 'Libya', 'Liechtenstein',
    'Lithuania', 'Luxembourg', 'Macau', 'Macedonia',
    'Madagascar', 'Malawi', 'Malaysia', 'Maldives', 'Mali',
    'Malta', 'Mars', 'Marshall-Islands', 'Martinique',
    'Mauritania', 'Mauritius', 'Mayotte', 'Mexico', 'Micronesia',
    'Moldova', 'Monaco', 'Mongolia', 'Montenegro', 'Montserrat',
    'Morocco', 'Mozambique', 'Myanmar', 'NATO',
    'Nagorno-Karabakh', 'Namibia', 'Nauru', 'Nepal',
    'Netherlands-Antilles', 'Netherlands', 'New-Caledonia',
    'New-Zealand', 'Nicaragua', 'Niger', 'Nigeria', 'Niue',
    'Norfolk-Island', 'North-Korea', 'Northern-Cyprus',
    'Northern-Mariana-Islands', 'Norway', 'Olympics', 'Oman',
    'Pakistan', 'Palau', 'Palestine', 'Panama',
    'Papua-New-Guinea', 'Paraguay', 'Peru', 'Philippines',
    'Pitcairn-Islands', 'Poland', 'Portugal', 'Puerto-Rico',
    'Qatar', 'Red-Cross', 'Republic-of-the-Congo', 'Romania',
    'Russia', 'Rwanda', 'Saint-Barthelemy', 'Saint-Helena',
    'Saint-Kitts-and-Nevis', 'Saint-Lucia', 'Saint-Martin',
    'Saint-Vincent-and-the-Grenadines', 'Samoa', 'San-Marino',
    'Sao-Tome-and-Principe', 'Saudi-Arabia', 'Scotland',
    'Senegal', 'Serbia', 'Seychelles', 'Sierra-Leone',
    'Singapore', 'Slovakia', 'Slovenia', 'Solomon-Islands',
    'Somalia', 'Somaliland', 'South-Africa',
    'South-Georgia-and-the-South-Sandwich-Islands',
    'South-Korea', 'South-Ossetia', 'South-Sudan', 'Spain',
    'Sri-Lanka', 'Sudan', 'Suriname', 'Swaziland', 'Sweden',
    'Switzerland', 'Syria', 'Taiwan', 'Tajikistan', 'Tanzania',
    'Thailand', 'Togo', 'Tokelau', 'Tonga',
    'Trinidad-and-Tobago', 'Tunisia', 'Turkey', 'Turkmenistan',
    'Turks-and-Caicos-Islands', 'Tuvalu', 'US-Virgin-Islands',
    'Uganda', 'Ukraine', 'United-Arab-Emirates',
    'United-Kingdom', 'United-Nations', 'United-States',
    'Unknown', 'Uruguay', 'Uzbekistan', 'Vanuatu',
    'Vatican-City', 'Venezuela', 'Vietnam', 'Wales',
    'Wallis-And-Futuna', 'Western-Sahara', 'Yemen', 'Zambia',
    'Zimbabwe'
]

LANGUAGES = [
    'aa', 'ab', 'ae', 'af', 'ak', 'am', 'an', 'ar', 'as', 'av', 'ay', 'az',
    'ba', 'be', 'bg', 'bh', 'bi', 'bm', 'bn', 'bo', 'br', 'bs', 'ca', 'ce',
    'ch', 'co', 'cr', 'cs', 'cu', 'cv', 'cy', 'da', 'de', 'dv', 'dz', 'ee',
    'el', 'en', 'eo', 'es', 'et', 'eu', 'fa', 'ff', 'fi', 'fj', 'fo', 'fr',
    'fy', 'ga', 'gd', 'gl', 'gn', 'gu', 'gv', 'ha', 'he', 'hi', 'ho', 'hr',
    'ht', 'hu', 'hy', 'hz', 'ia', 'id', 'ie', 'ig', 'ii', 'ik', 'io', 'is',
    'it', 'iu', 'ja', 'jv', 'ka', 'kg', 'ki', 'kj', 'kk', 'kl', 'km', 'kn',
    'ko', 'kr', 'ks', 'ku', 'kv', 'kw', 'ky', 'la', 'lb', 'lg', 'li', 'ln',
    'lo', 'lt', 'lu', 'lv', 'mg', 'mh', 'mi', 'mk', 'ml', 'mn', 'mr', 'ms',
    'mt', 'my', 'na', 'nb', 'nd', 'ne', 'ng', 'nl', 'nn', 'no', 'nr', 'nv',
    'ny', 'oc', 'oj', 'om', 'or', 'os', 'pa', 'pi', 'pl', 'ps', 'pt', 'qu',
    'rm', 'rn', 'ro', 'ru', 'rw', 'sa', 'sc', 'sd', 'se', 'sg', 'si', 'sk',
    'sl', 'sm', 'sn', 'so', 'sq', 'sr', 'ss', 'st', 'su', 'sv', 'sw', 'ta',
    'te', 'tg', 'th', 'ti', 'tk', 'tl', 'tn', 'to', 'tr', 'ts', 'tt', 'tw',
    'ty', 'ug', 'uk', 'ur', 'uz', 've', 'vi', 'vo', 'wa', 'wo', 'xh', 'yi',
    'yo', 'za', 'zh', 'zu'
]


def add_error(msg, errors):
    """Add error to the list of errors."""
    errors.append(msg)


def add_suberror(msg, errors):
    """Add sub error, ie. error indented by 1 level ("\t"), to the list of errors."""
    errors.append("\t{0}".format(msg))


def look_for_fixme(func):
    '''Decorator to fail test if text argument starts with "FIXME".'''
    def inner(arg):
        if (arg is not None) and \
           isinstance(arg, our_basestring) and \
           arg.lstrip().startswith('FIXME'):
            return False
        return func(arg)
    return inner


@look_for_fixme
def check_layout(layout):
    '''"layout" in YAML header must be "workshop".'''

    return layout == 'workshop'


@look_for_fixme
def check_root(root):
    '''"root" (the path from this page to the root directory) must be "."'''

    return root == '.'


@look_for_fixme
def check_country(country):
    '''"country" must be a hyphenated full country name from the list
    embedded in this script.'''

    return country in COUNTRIES


@look_for_fixme
def check_language(language):
    '''"language" must be one of the two-letter ISO 639-1 language codes
    embedded in this script.'''

    return language in LANGUAGES


@look_for_fixme
def check_humandate(date):
    '''"humandate" must be a human-readable date with a 3-letter month and
    4-digit year.  Examples include "Feb 18-20, 2025" and "Feb 18 and
    20, 2025".  It may be in languages other than English, but the
    month name should be kept short to aid formatting of the main
    Software Carpentry web site.'''

    if "," not in date:
        return False

    month_dates, year = date.split(",")

    # The first three characters of month_dates are not empty
    month = month_dates[:3]
    if any(char == " " for char in month):
        return False

    # But the fourth character is empty ("February" is illegal)
    if month_dates[3] != " ":
        return False

    # year contains *only* numbers
    try:
        int(year)
    except:
        return False

    return True


@look_for_fixme
def check_humantime(time):
    '''"humantime" is a human-readable start and end time for the workshop,
    such as "09:00 - 16:00".'''

    return bool(re.match(HUMANTIME_PATTERN, time.replace(" ", "")))


def check_date(this_date):
    '''"startdate" and "enddate" are machine-readable start and end dates for
    the workshop, and must be in YYYY-MM-DD format, e.g., "2015-07-01".'''

    from datetime import date
    # yaml automatically loads valid dates as datetime.date
    return isinstance(this_date, date)


@look_for_fixme
def check_latitude_longitude(latlng):
    '''"latlng" must be a valid latitude and longitude represented as two
    floating-point numbers separated by a comma.'''

    try:
        lat, lng = latlng.split(',')
        lat = float(lat)
        long = float(lng)
    except ValueError:
        return False
    return (-90.0 <= lat <= 90.0) and (-180.0 <= long <= 180.0)


def check_instructors(instructors):
    '''"instructor" must be a non-empty comma-separated list of quoted names,
    e.g. ['First name', 'Second name', ...'].  Do not use "TBD" or other
    placeholders.'''

    # yaml automatically loads list-like strings as lists
    return isinstance(instructors, list) and len(instructors) > 0


def check_helpers(helpers):
    '''"helper" must be a comma-separated list of quoted names,
    e.g. ['First name', 'Second name', ...'].  The list may be empty.  Do
    not use "TBD" or other placeholders.'''

    # yaml automatically loads list-like strings as lists
    return isinstance(helpers, list) and len(helpers) >= 0


@look_for_fixme
def check_email(email):
    '''"contact" must be a valid email address consisting of characters, a
    @, and more characters.  It should not be the default contact
    email address "admin@software-carpentry.org".'''

    return bool(re.match(EMAIL_PATTERN, email)) and \
           (email != DEFAULT_CONTACT_EMAIL)


def check_eventbrite(eventbrite):
    '''"eventbrite" (the Eventbrite registration key) must be 9 or more digits.'''

    if isinstance(eventbrite, int):
        return True
    else:
        return bool(re.match(EVENTBRITE_PATTERN, eventbrite))


@look_for_fixme
def check_etherpad(etherpad):
    '''"etherpad" must be a valid URL.'''

    return bool(re.match(URL_PATTERN, etherpad))


@look_for_fixme
def check_pass(value):
    '''This test always passes (it is used for "checking" things like
    addresses, for which no sensible validation is feasible).'''

    return True


HANDLERS = {
    'layout':     (True, check_layout, 'layout isn\'t "workshop"'),
    'root':       (True, check_root, 'root can only be "."'),
    'country':    (True, check_country,
                   'country invalid: must use full hyphenated name from: ' +
                   ' '.join(COUNTRIES)),

    'language' :  (False,  check_language,
                   'language invalid: must be a ISO 639-1 code'),

    'humandate':  (True, check_humandate,
                   'humandate invalid. Please use three-letter months like ' +
                   '"Jan" and four-letter years like "2025".'),
    'humantime':  (True, check_humantime,
                   'humantime doesn\'t include numbers'),
    'startdate':  (True, check_date,
                   'startdate invalid. Must be of format year-month-day, ' +
                   'i.e., 2014-01-31.'),
    'enddate':    (False, check_date,
                   'enddate invalid. Must be of format year-month-day, i.e.,' +
                   ' 2014-01-31.'),

    'latlng':     (True, check_latitude_longitude,
                   'latlng invalid. Check that it is two floating point ' +
                   'numbers, separated by a comma.'),

    'instructor': (True, check_instructors,
                   'instructor list isn\'t a valid list of format ' +
                   '["First instructor", "Second instructor",..].'),
    'helper':     (True, check_helpers,
                   'helper list isn\'t a valid list of format ' +
                   '["First helper", "Second helper",..].'),

    'contact':    (True, check_email,
                   'contact email invalid or still set to ' +
                   '"{0}".'.format(DEFAULT_CONTACT_EMAIL)),

    'eventbrite': (False, check_eventbrite, 'Eventbrite key appears invalid.'),
    'etherpad':   (False, check_etherpad, 'Etherpad URL appears invalid.'),
    'venue':      (False, check_pass, 'venue name not specified'),
    'address':    (False, check_pass, 'address not specified'),
    'day1_am':    (False, check_pass, 'day1_am not specified'),
    'day1_pm':    (False, check_pass, 'day1_pm not specified'),
    'day2_am':    (False, check_pass, 'day2_am not specified'),
    'day2_pm':    (False, check_pass, 'day2_pm not specified')
}

# REQUIRED is all required categories.
REQUIRED = set([k for k in HANDLERS if HANDLERS[k][0]])

# OPTIONAL is all optional categories.
OPTIONAL = set([k for k in HANDLERS if not HANDLERS[k][0]])


def check_validity(data, function, errors, error_msg):
    '''Wrapper-function around the various check-functions.'''
    valid = function(data)
    if not valid:
        add_error(error_msg, errors)
        add_suberror('Offending entry is: "{0}"'.format(data), errors)
    return valid


def check_blank_lines(raw_data, errors, error_msg):
    '''Blank lines are not allowed in category headers.'''
    lines = [x.strip() for x in raw_data.split('\n')]
    if '' in lines:
        add_error(error_msg, errors)
        add_suberror('{0} blank lines found in header'.format(lines.count('')), errors)
        return False
    return True


def check_categories(left, right, errors, error_msg):
    '''Report set difference of categories.'''
    result = left - right
    if result:
        add_error(error_msg, errors)
        add_suberror('Offending entries: {0}'.format(result), errors)
        return False
    return True


def get_header(text):
    '''Extract YAML header from raw data, returning (None, None) if no
    valid header found and (raw, parsed) if header found.'''

    # YAML header must be right at the start of the file.
    if not text.startswith('---'):
        return None, None

    # YAML header must start and end with '---'
    pieces = text.split('---')
    if len(pieces) < 3:
        return None, None

    # Return raw text and YAML-ized form.
    raw = pieces[1].strip()
    return raw, yaml.load(raw)


def check_file(filename, data):
    '''Get header from index.html, call all other functions and check file
    for validity. Return list of errors (empty when no errors).'''

    errors = []
    raw, header = get_header(data)
    if header is None:
        msg = ('Cannot find YAML header in given file "{0}".'.format(filename))
        add_error(msg, errors)
        return errors

    # Do we have any blank lines in the header?
    is_valid = check_blank_lines(raw, errors,
                                 'There are blank lines in the header')

    # Look through all header entries.  If the category is in the input
    # file and is either required or we have actual data (as opposed to
    # a commented-out entry), we check it.  If it *isn't* in the header
    # but is required, report an error.
    for category in HANDLERS:
        required, handler_function, error_message = HANDLERS[category]
        if category in header:
            if required or header[category]:
                is_valid &= check_validity(header[category],
                                           handler_function, errors,
                                           error_message)
        elif required:
            msg = 'index file is missing mandatory key "{0}"'.format(category)
            add_error(msg, errors)
            is_valid = False

    # Check whether we have missing or too many categories
    seen_categories = set(header.keys())

    is_valid &= check_categories(REQUIRED, seen_categories, errors,
                                 'There are missing categories')

    is_valid &= check_categories(seen_categories, REQUIRED.union(OPTIONAL),
                                 errors, 'There are superfluous categories')

    return errors


def main():
    '''Run as the main program.'''
    filename = None
    if len(sys.argv) == 1:
        if os.path.exists('./index.html'):
            filename = './index.html'
        elif os.path.exists('../index.html'):
            filename = '../index.html'
    elif len(sys.argv) == 2:
        filename = sys.argv[1]

    if filename is None:
        print(USAGE, file=sys.stderr)
        sys.exit(1)

    logger.info('Testing "{0}"'.format(filename))

    with open(filename) as reader:
        data = reader.read()
        errors = check_file(filename, data)

    if errors:
        for m in errors:
            logger.error(m)
        sys.exit(1)
    else:
        logger.info('Everything seems to be in order')
        sys.exit(0)


if __name__ == '__main__':
    main()
