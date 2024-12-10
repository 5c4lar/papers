# papers
Automatically collecting and summarizing papers

## Usage

Example:

```sh
# gather abstracts
python3 -m src --path data/ndss24 --conf ndss --year 2024 --process 100   
# concat datasets
python3 src/concat.py --datasets data/uss24 data/sp24 data/ccs24 data/ndss24 --output data/24     
# classify papers
python3 -m src.label --dataset data/24 --output data/24_label                        
# search papers
python3 -m src.search --dataset data/ndss24 --query "papers about llm security" --output data/ndss24_search.jsonl --max-workers 10
# import papers to notion
python -m src.notion --database_id notion_database_id --input_path data/ndss24_label
python -m src.notion --database_id notion_database_id --input_path data/ndss24_search.jsonl
```

