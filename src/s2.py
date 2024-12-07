import requests


def s2_title_search(title):
    url = f"https://api.semanticscholar.org/graph/v1/paper/search/match?query={
        title}"
    response = requests.get(url)
    if response.status_code == 200:
        id = response.json()['data'][0]
        print(id)
        return id
    return None


def s2_abstracts(ids):
    url = 'https://api.semanticscholar.org/graph/v1/paper/batch'
    params = {"fields": 'abstract,title'}
    response = requests.post(
        url,
        params=params,
        json={"ids": ids}
    )
    return response.json()
