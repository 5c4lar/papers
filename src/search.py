import argparse
import json
from typing import Any, Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed

import datasets
import instructor
from openai import OpenAI
from pydantic import BaseModel
from tqdm import tqdm

from src.utils import call_llm
from src.config import InstructorConfig, OpenaiConfig


class RelevanceCheck(BaseModel):
    relevant: bool


class PaperSemanticSearch:
    def __init__(self, dataset_path: str, max_workers: int = 5):
        """
        Initialize the semantic search engine

        Args:
            dataset_path: Path to the datasets file
            max_workers: Maximum number of concurrent threads
        """
        self.dataset = datasets.load_from_disk(dataset_path)
        self.max_workers = max_workers

    def _get_paper_content(self, paper: Dict[str, Any]) -> str:
        """Get formatted paper content for comparison"""
        return f"""Title: {paper['title']}
                Abstract: {paper.get('abstract', 'N/A')}"""

    def _extract_relevance_check(self, prompt: str) -> RelevanceCheck:
        client = instructor.from_openai(
            OpenAI(base_url=OpenaiConfig.base_url, api_key=OpenaiConfig.api_key)
        )

        response = client.chat.completions.create(
            model=InstructorConfig.model_name,
            response_model=RelevanceCheck,
            messages=[{"role": "user", "content": prompt}],
        )
        return response

    def _check_relevance(self, query: str, paper_content: str) -> bool:
        """
        Use LLM to check if a paper is relevant to the query

        Args:
            query: User's search query or description
            paper_content: Paper's content (title + abstract)

        Returns:
            bool: Whether the paper is relevant
        """
        prompt = f"""Please analyze if the following academic paper is relevant to this query/topic:
                    Query/Topic: {query}
                    Paper:
                    {paper_content}
                    Please respond with only 'yes' if the paper is relevant, or 'no' if it's not relevant."""

        messages = [
            {"role": "user", "content": prompt},
        ]
        response = call_llm(
            messages=messages,
        )
        return self._extract_relevance_check(response)

    def search(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for relevant papers based on the query using multiple threads

        Args:
            query: Search query or description of the topic

        Returns:
            List of relevant papers
        """
        relevant_papers = []
        papers_list = list(self.dataset)

        def process_paper(paper):
            paper_content = self._get_paper_content(paper)
            try:
                if self._check_relevance(query, paper_content).relevant:
                    return {
                        "title": paper.get("title", "N/A"),
                        "abstract": paper.get("abstract", "N/A"),
                        "year": paper.get("year", "N/A"),
                        "conf": paper.get("conf", "N/A"),
                    }
            except Exception as e:
                print(
                    f"Error processing paper {paper.get('title', 'Unknown')}: {str(e)}"
                )
            return None

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_paper = {
                executor.submit(process_paper, paper): paper for paper in papers_list
            }

            with tqdm(total=len(papers_list), desc="Searching papers") as pbar:
                for future in as_completed(future_to_paper):
                    result = future.result()
                    if result:
                        relevant_papers.append(result)
                    pbar.update(1)

        return relevant_papers


def main():
    parser = argparse.ArgumentParser(
        description="Search for relevant papers in the security conference dataset"
    )
    parser.add_argument(
        "--dataset", type=str, required=True, help="Path to the dataset file"
    )
    parser.add_argument(
        "--query", type=str, required=True, help="Search query or description"
    )
    parser.add_argument(
        "--output", type=str, required=True, help="Path to the output file"
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=5,
        help="Maximum number of concurrent threads",
    )

    args = parser.parse_args()

    searcher = PaperSemanticSearch(
        dataset_path=args.dataset, max_workers=args.max_workers
    )

    query = args.query
    results = searcher.search(query)

    print(f"\nFound {len(results)} relevant papers:")
    for i, paper in enumerate(results, 1):
        print(f"\n{i}. {paper['title']}")
        print(f"conf: {paper['conf']} ({paper['year']})")
        print(
            "Abstract:",
            paper["abstract"][:200] + "..."
            if len(paper["abstract"]) > 200
            else paper["abstract"],
        )

    # save results to jsonl
    with open(args.output, "w") as f:
        for paper in results:
            f.write(json.dumps(paper) + "\n")


if __name__ == "__main__":
    main()
