import requests

from bs4 import BeautifulSoup

# Volleyball
volleyball_url = "https://buchsys.sport.uni-karlsruhe.de/angebote/aktueller_zeitraum/_Volleyball.html"
volleyball_ids = ['6801', '6802', '6803', '6804', '6805', '6806', '6807']


def check(url, ids):
    sport = url.split("_")[-1].split(".")[0]
    res = requests.get(url)
    html_doc = res.text
    soup = BeautifulSoup(html_doc, 'html.parser')

    result = []

    for id in ids:
        course = soup.find(text=id).parent.parent
        name = course.find("td", {"class": "bs_sdet"}).text
        button = course.find("input", {"class": "bs_btn_warteliste"})
        if button:
            result.append((False, sport, name))
        else:
            result.append((True, sport, name))

    return result, soup.prettify()


def get_ids():
    check_results = []

    res, html = check(volleyball_url, volleyball_ids)

    for u in res:
        check_results.append(u)

    return check_results, html


if __name__ == '__main__':
    print(get_ids())
