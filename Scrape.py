import requests

from bs4 import BeautifulSoup

# Volleyball
url2 = "https://buchsys.sport.uni-karlsruhe.de/angebote/aktueller_zeitraum/_Volleyball.html"
id2 = ['6801', '6802', '6803', '6804', '6805', '6806', '6807']
# Schwimmen
url3 = "https://buchsys.sport.uni-karlsruhe.de/angebote/aktueller_zeitraum/_Schwimmen.html"
id3 = ["5102", "5103", "5104"]
# Tischtennis
url = r'https://buchsys.sport.uni-karlsruhe.de/angebote/aktueller_zeitraum/_Tischtennis.html'
id1 = ["6202", "6203", "6204"]


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

    tt_res, tt_html = check(url, id1)

    for u in tt_res:
        check_results.append(u)
    for u in check(url2, id2)[0]:
        check_results.append(u)
    for u in check(url3, id3)[0]:
        check_results.append(u)

    # tt_html for debugging.
    return check_results, tt_html

if __name__ == '__main__':
    print(get_ids())
