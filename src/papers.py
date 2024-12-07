import requests
from bs4 import BeautifulSoup

def get_ccs_papers():
    url = "https://www.sigsac.org/ccs/CCS2024/program/accepted-papers.html"
    response = requests.get(url)
    titles = []
    if response.status_code == 200:
        html = BeautifulSoup(response.text, 'html.parser')
        tables = html.find_all('table')
        for table in tables:
            tds = table.find_all('td')
            for td in tds[::2]:
                titles.append(td.text)
    return titles
