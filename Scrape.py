import requests

from bs4 import BeautifulSoup


def get_html(url):
    res = requests.get(url)
    return res.text


def check(html, ids):
    soup = BeautifulSoup(html, 'html.parser')
    result = {}

    for id in ids:
        course = soup.find(text=id).parent.parent
        name = course.find("td", {"class": "bs_sdet"}).text
        button = course.find("input", {"class": "bs_btn_buchen"})
        if button:
            result[name] = "Frei"
        else:
            result[name] = "Voll"

    return result
