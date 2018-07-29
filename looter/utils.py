import time
import uuid
import functools
from urllib.parse import unquote
import requests
import aiohttp
from fake_useragent import UserAgent


def perf(f):
    """
    A decorator to measure the performance of a specific function.
    """
    @functools.wraps(f)
    def wr(*args, **kwargs):
        start = time.time()
        r = f(*args, **kwargs)
        end = time.time()
        print(f'Time elapsed: {end - start}')
        return r
    return wr


def ensure_schema(url: str) -> str:
    """Ensure the url starts with a http schema.
    
    Args:
        url (str): A url without http schema such as konachan.com.
    
    Returns:
        str: A url with http schema such as http://konachan.com.
    """
    if not (url.startswith('http') or url.startswith('https')):
        return f'http://{url}'
    else:
        return url


def get_domain(url: str) -> str:
    """Get the domain(hostname) of the site.
    
    Args:
        url (str): A url with http schema.
    
    Returns:
        str: the domain(hostname) of the site.
    """
    url = url[8:] if url.startswith('https') else url[7:]
    domain = f"http://{url.split('/')[0]}"
    return domain


def send_request(url: str, timeout=60, use_proxies=False, headers=None) -> requests.models.Response:
    """Send an HTTP request to a url.
    
    Args:
        url (str): The url of the site.
        timeout (int, optional): Defaults to 60. The maxium time of request.
        headers (optional): Defaults to fake-useragent, can be customed by user.

    Returns:
        requests.models.Response: The response of the HTTP request.
    """
    if not headers:
        headers = {'User-Agent': UserAgent().random}
    url = ensure_schema(url)
    res = requests.get(url, headers=headers, timeout=timeout)
    res.raise_for_status()
    return res


def rectify(name: str) -> str:
    """
    Get rid of illegal symbols of a filename.

    Args:
        name (str): The filename.

    Returns:
        The rectified filename.
    """
    name = ''.join([c for c in unquote(name) if c not in {'?', '<', '>', '|', '*', '"', ":"}])
    return name


def get_img_info(url: str, max_length=160) -> tuple:
    """Get the info of an image.

    Args:
        url (str): The url of the site.
        max_length (int, optional): Defaults to 160. The maximal length of the filename.

    Returns:
        tuple: The url of an image and its name.
    """
    if hasattr(url, 'tag') and url.tag == 'a':
        url = url.get('href')
    elif hasattr(url, 'tag') and url.tag == 'img':
        url = url.get('src')
    name = ensure_schema(url).split('/')[-1]
    fname, ext = rectify(name).rsplit('.', 1)
    name = f'{fname[:max_length]}.{ext}'
    return url, name


@perf
def save_img(url: str, random_name=False):
    """
    Download image and save it to local disk.

    Args:
        url (str): The url of the site.
        random_name (int, optional): Defaults to False. If names of images are duplicated, use this.
    """
    url, name = get_img_info(url)
    if random_name:
        name = f'{name[:-4]}{str(uuid.uuid1())[:8]}{name[-4:]}'
    with open(name, 'wb') as f:
        f.write(send_request(url).content)
        print(f'Saved {name}')


async def async_save_img(url: str, random_name=False):
    """Save an image in an async style.

    Args:
        url (str): The url of the site.
        random_name (int, optional): Defaults to False. If names of images are duplicated, use this.
    """
    headers = {'User-Agent': UserAgent().random}
    url, name = get_img_info(url)
    if random_name:
        name = f'{name[:-4]}{str(uuid.uuid1())[:8]}{name[-4:]}'
    with open(name, 'wb') as f:
        async with aiohttp.ClientSession() as ses:
            async with ses.get(url, headers=headers) as res:
                data = await res.read()
                f.write(data)
                print(f'Saved {name}')