import datasets

def main():
    import argparse
    import datasets
    parser = argparse.ArgumentParser()
    parser.add_argument("--datasets", nargs="+", help="Path to the dataset")
    parser.add_argument("--output", help="Path to the output")
    args = parser.parse_args()
    
    ds = datasets.concatenate_datasets([datasets.load_from_disk(dataset) for dataset in args.datasets])
    ds.save_to_disk(args.output)
    
if __name__ == "__main__":
    main()