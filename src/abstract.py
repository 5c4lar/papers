"""
Test: python3 -m top4grep.abstract
"""
import re
import requests
from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urlunparse
import logging


def get_id(url):
    parsed_url = urlparse(url)
    doi = parsed_url.path.lstrip("/")  # Remove the leading "/"
    return doi


logger = logging.getLogger("PaperAbstract")


class BasePaperAbstract(ABC):
    @abstractmethod
    def get_abstract(self, url, authors):
        pass


class SemanticScholarAbstract(BasePaperAbstract):
    def get_abstract(self, url, authors):
        doi = get_id(url)
        sem_url = f"https://api.semanticscholar.org/v1/paper/{doi}"
        response = requests.get(sem_url)
        if response.status_code == 200:
            data = response.json()
            abstract = data.get("abstract", "No abstract available")
            return abstract
        else:
            return None


class AbstractNDSS(BasePaperAbstract):
    def get_abstract(self, url, authors):
        logger.debug(f'URL: {url}')
        r = requests.get(url)
        assert r.status_code == 200

        html = BeautifulSoup(r.text, 'html.parser')
        paper_data = html.find('div', {'class': 'paper-data'})
        if paper_data is not None:
            # abstract_paragraphs = filter(lambda x: x.text != '', paper_data.find_all('p')[1:])
            paper_data.find_next('p').replace_with('')
            return paper_data.text.rstrip().lstrip()
        else:
            abstract_paragraphs = html.find(string=re.compile(
                "Abstract:")).find_next(recursive=False)
            return abstract_paragraphs.get_text(separator='\n')


class AbstractUSENIX(BasePaperAbstract):
    def get_abstract(self, url, authors):
        r = requests.get(url)
        logger.debug(f'URL: {url}')
        assert r.status_code == 200

        html = BeautifulSoup(r.text, 'html.parser')

        abstract_paragraphs = html.find(string=re.compile(
            "Abstract:")).find_next(recursive=False)
        return abstract_paragraphs.get_text(separator='\n')


class AbstractCCS(BasePaperAbstract):
    def get_abstract(self, url, authors):
        # TODO: ACM library doesn't like me to crawl and will ban me when upset.
        logger.debug(f'URL: {url}')
        r = requests.get(url)
        assert r.status_code == 200

        html = BeautifulSoup(r.text, 'html.parser')
        paragraphs = html.find('section', {'id': 'abstract'}).find_all(
            'div', role='paragraph')
        return '\n'.join(paragraph.get_text(strip=True) for paragraph in paragraphs)


NDSS = AbstractNDSS()
SP = SemanticScholarAbstract()
USENIX = AbstractUSENIX()
CCS = AbstractCCS()

Abstracts = {'ndss': NDSS,
             'sp': SP,
             'uss': USENIX,
             'ccs': CCS}


def get_abstract(conf, url):
    extractor = Abstracts[conf]
    return extractor.get_abstract(url, [])


def process_paper(args):
    conf, paper = args
    url = paper['info']['ee']
    try:
        abstract = get_abstract(conf, url)
        return {"title": paper['info']['title'], 'abstract': abstract}
    except Exception as e:
        logger.error(f"Failed to process: {
                     paper['info']['title']}, url: {url}")
        print(e)
        return None


if __name__ == '__main__':
    logger.setLevel('DEBUG')
    # SP.get_abstract('https://doi.ieeecomputersociety.org/10.1109/SP46215.2023.00131', [])
    # SP.get_abstract('https://doi.org/10.1109/SP46215.2023.10179411', [])
    # print(SP.get_abstract('https://doi.org/10.1109/SP54263.2024.00030', []))
    # print(USENIX.get_abstract('https://www.usenix.org/conference/usenixsecurity24/presentation/zou', []))
    # print(CCS.get_abstract('https://doi.org/10.1145/3576915.3616615', []))
    print(NDSS.get_abstract(
        'https://www.ndss-symposium.org/ndss-paper/unus-pro-omnibus-multi-client-searchable-encryption-via-access-control/', []))
