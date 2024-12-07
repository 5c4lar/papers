from src.dblp import get_json
from src.abstract import *
from src.s2 import *
from src.papers import *
from multiprocessing import Pool
import json
from tqdm import tqdm
import datasets
import pathlib


def get_ids(conf, data, process=8):
    match conf:
        case 'uss' | 'ndss':
            ids = []
            titles = [paper['info']['title'] for paper in data]
            with Pool(process) as pool, tqdm(total=len(titles)) as pbar:
                for result in pool.imap_unordered(s2_title_search, titles):
                    pbar.update()
                    pbar.refresh()
                    if result is not None:
                        ids.append(result['paperId'])
        case 'ccs':
            ids = []
            titles = get_ccs_papers()
            with Pool(process) as pool, tqdm(total=len(titles)) as pbar:
                for result in pool.imap_unordered(s2_title_search, titles):
                    pbar.update()
                    pbar.refresh()
                    if result is not None:
                        ids.append(result['paperId'])
        case 'sp':
            ids = [paper['info']['doi'] for paper in data]
    return ids


def get_abstracts(conf, data, process=8):
    with Pool(process) as pool, tqdm(total=len(data)) as pbar:
        results = []
        for result in pool.imap_unordered(process_paper, [(conf, paper) for paper in data]):
            pbar.update()
            pbar.refresh()
            if result is not None:
                results.append(result)
    return results


def process_papers(conf, data, process=8):
    match conf:
        case 'sp' | 'ccs':
            ids = get_ids(conf, data, process)
            results = s2_abstracts(ids)
        case 'uss' | 'ndss':
            results = get_abstracts(conf, data, process)
    # results = sch.get_papers(ids)
    return results


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--library_id", help="library id of the account")  # 9467597
    parser.add_argument("--library_type", default="user",
                        help="Accessing user library or group library?")
    # 7dqMME5kwR9nMYbGZlXQCc4H
    parser.add_argument("--api_key", help="API Key")
    parser.add_argument("--abstract", action="store_true")
    parser.add_argument("--conf", type=str, default="uss")
    parser.add_argument("--year", type=int, default=2024)
    parser.add_argument("--process", type=int)
    parser.add_argument("--path", type=str, help="Path to the datasets")
    args = parser.parse_args()

    path = pathlib.Path(args.path)

    data = get_json(args.conf, args.year)

    data = [paper for paper in data if paper['info']['type'] != 'Editorship']

    results = process_papers(args.conf, data, args.process)

    def gen():
        for result in results:
            if result is not None:
                yield {"title": result["title"], "abstract": result["abstract"], "year": args.year, "conf": args.conf}
    ds = datasets.Dataset.from_generator(gen)
    ds.save_to_disk(path)

if __name__ == "__main__":
    main()
