# %%
from docling.document_converter import DocumentConverter
from docling_core.transforms.chunker import HierarchicalChunker

converter = DocumentConverter()
chunker = HierarchicalChunker()


def parse_pdf(file):
    conv_res = converter.convert(file)
    doc = conv_res.document
    chunks = list(chunker.chunk(doc))
    abstract_content = []
    for chunk in chunks:
        if chunk.meta.headings and chunk.meta.headings[0] == 'Abstract':
            abstract_content.append(chunk.text)
    abstract = '\n'.join(abstract_content)
    return abstract

# %%


def main():
    import argparse
    import datasets
    from multiprocessing import Pool
    from tqdm import tqdm
    import pathlib
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", help="Directory to the pdf")
    parser.add_argument("--path", help="Directory to the output")
    parser.add_argument("--process", type=int)
    args = parser.parse_args()

    files = list(pathlib.Path(args.dir).rglob("*.pdf"))
    abstracts = []
    with Pool(args.process) as pool, tqdm(total=len(files)) as pbar:
        for result in pool.imap_unordered(parse_pdf, files):
            pbar.update()
            pbar.refresh()
            if result is not None:
                abstracts.append(result)
    print(abstracts)


if __name__ == "__main__":
    main()
