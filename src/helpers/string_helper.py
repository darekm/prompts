import datetime
import re


def find_between(s, first, last):
    try:
        start = s.index(first) + len(first)
        end = s.index(last, start)
        return s[start:end]
    except ValueError:
        return ''


def compare_json(left, right):
    result = []
    for key in left:
        if left[key] != right.get(key):
            if key == 'details':
                for idx in range(len(left[key])):
                    if idx > len(right[key]):
                        result.append({'details': idx, 'error': 'longer', 'left': left[key][idx]})
                    else:
                        result += compare_json(left[key][idx], right[key][idx])

                        # result.append({'details': idx, 'error': compare_json(left[key][idx], right[key][idx])})
                if len(left[key]) < len(right[key]):
                    result.append({'details': len(right[key]), 'error': 'shorter', 'len': len(left[key])})
            else:
                # print(f' {left[key]}   <> {right.get(key)}')
                result.append({'left': left[key], 'right': right[key]})
    return result


def normalize_number(num_str):
    if not num_str:
        return num_str
    if isinstance(num_str, float):
        return num_str

    # Replace comma with dot if comma is used as decimal separator
    if (len(num_str) > 3) and ('.' not in num_str) and (',' not in num_str) and (num_str[-3] == ' '):
        num_str = num_str[:-3] + '.' + num_str[-2:]
    if num_str.find(',') < num_str.find('.') and ',' in num_str:
        num_str = num_str.replace(',', '')
    if num_str.find('.') < num_str.find(',') and '.' in num_str:
        num_str = num_str.replace('.', '')
    if ',' in num_str and '.' not in num_str:
        num_str = num_str.replace(',', '.')
    # Remove any non-numeric characters except for the dot
    num_str = re.sub(r'[^\d.-]', '', num_str)
    # Convert to float
    # return float(num_str)
    return num_str


def string2float(_str):
    try:
        if isinstance(_str, str):
            _norm = normalize_number(_str)
            return float(_norm)
        if isinstance(_str, float):
            return _str
        return 8e9
    except ValueError:
        return 9e9


def mask_hour(hour):
    _dat = datetime.datetime.today() - datetime.timedelta(hours=hour)
    return _dat.strftime('%Y-%m-%d %H')


def replace_tab_char(s):
    return s.replace('\u0009', ' ')

def clean_url(url):
    _url = url.replace('http://', 'https://')
    _url = _url.split('#')[0]
    return _url


def url_frendly( tag_name: str) -> str:
        """
        Convert a tag name to a URL-friendly format.

        Args:
            tag_name: The name of the tag

        Returns:
            URL-friendly string
        """
        import re

        # Convert to lowercase
        result = tag_name.lower()
        # Replace polish characters
        polish_chars = {'ą': 'a', 'ć': 'c', 'ę': 'e', 'ł': 'l', 'ń': 'n', 'ó': 'o', 'ś': 's', 'ź': 'z', 'ż': 'z'}
        for pol, eng in polish_chars.items():
            result = result.replace(pol, eng)
        # Replace spaces with hyphens
        result = result.replace(' ', '-')
        # Remove any non-alphanumeric characters (except hyphens)
        result = re.sub(r'[^a-z0-9-]', '', result)
        # Replace multiple hyphens with single hyphen
        result = re.sub(r'-+', '-', result)
        # Remove leading and trailing hyphens
        result = result.strip('-')

        return result
