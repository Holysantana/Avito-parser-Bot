import requests
from bs4 import BeautifulSoup
from config import HEADERS
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def build_url(query: str, city: str, min_price=None, max_price=None):
    """
    Формируем URL поиска для doski.ru
    """

    base_url = "https://www.doski.ru"

    query_encoded = query.replace(" ", "+")
    city_encoded = city.replace(" ", "+")

    url = f"{base_url}/search.php?q={query_encoded}&c={city_encoded}"

    if min_price:
        url += f"&price_from={min_price}"
    if max_price:
        url += f"&price_to={max_price}"

    return url


def parse_doski(query: str, city: str, min_price=None, max_price=None):
    """
    Парсинг объявлений с doski.ru
    """

    url = build_url(query, city, min_price, max_price)

    try:
        response = requests.get(url, headers=HEADERS, timeout=10, verify=False)
    except Exception as e:
        print("Ошибка запроса:", e)
        return []

    if response.status_code != 200:
        print("Статус код:", response.status_code)
        return []

    soup = BeautifulSoup(response.text, "lxml")

    results = []

    links = soup.find_all("a", href=True)

    for link in links:
        href = link["href"]

        if "/msg/" in href:
            full_link = "https://www.doski.ru" + href

            if full_link not in results:
                results.append(full_link)

        if len(results) >= 10:
            break

    return results
