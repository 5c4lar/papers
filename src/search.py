import argparse
import json
from typing import Any, Dict, List

import aisuite as ai
import datasets
import instructor
from src.config import AisuiteConfig, InstructorConfig, ModelConfig, OpenaiConfig
from openai import OpenAI
from pydantic import BaseModel
from tqdm import tqdm


class RelevanceCheck(BaseModel):
    relevant: bool


class PaperSemanticSearch:
    def __init__(self, dataset_path: str):
        """
        Initialize the semantic search engine

        Args:
            dataset_path: Path to the datasets file
            openai_api_key: OpenAI API key. If not provided, will try to get from environment
        """
        self.dataset = datasets.load_from_disk(dataset_path)
        self.client = OpenAI(
            api_key=OpenaiConfig.api_key,
            base_url=OpenaiConfig.base_url,
        )

    def _get_paper_content(self, paper: Dict[str, Any]) -> str:
        """Get formatted paper content for comparison"""
        return f"""Title: {paper['title']}
                Abstract: {paper.get('abstract', 'N/A')}"""

    def _extract_relevance_check(self, prompt: str) -> RelevanceCheck:
        client = instructor.from_openai(OpenAI(base_url=OpenaiConfig.base_url))
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

        provider_configs = {
            "openai": {
                "base_url": OpenaiConfig.base_url,
                "api_key": OpenaiConfig.api_key,
            }
        }
        client = ai.Client(provider_configs=provider_configs)

        messages = [
            {"role": "user", "content": prompt},
        ]
        response = client.chat.completions.create(
            model=AisuiteConfig.model_name,
            messages=messages,
            temperature=ModelConfig.temperature,
        )
        return self._extract_relevance_check(response.choices[0].message.content)

    def search(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for relevant papers based on the query

        Args:
            query: Search query or description of the topic
            max_papers: Maximum number of papers to return

        Returns:
            List of relevant papers
        """
        relevant_papers = []

        for paper in tqdm(self.dataset, desc="Searching papers"):
            paper_content = self._get_paper_content(paper)

            if self._check_relevance(query, paper_content).relevant:
                paper_dict = {
                    "title": paper.get("title", "N/A"),
                    "abstract": paper.get("abstract", "N/A"),
                    "year": paper.get("year", "N/A"),
                    "conf": paper.get("conf", "N/A"),
                }
                relevant_papers.append(paper_dict)

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

    args = parser.parse_args()

    searcher = PaperSemanticSearch(dataset_path=args.dataset)

    query = args.query
    results = searcher.search(query)

    print(f"\nFound {len(results)} relevant papers:")
    for i, paper in enumerate(results, 1):
        print(f"\n{i}. {paper['title']}")
        print(f"Venue: {paper['venue']} ({paper['year']})")
        print(f"URL: {paper['url']}")
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
