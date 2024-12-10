import argparse
import json
import os
from pathlib import Path
from typing import Any, Iterator, Optional

import datasets
from notion_client import Client
from rich.console import Console

console = Console()


class NotionClient:
    """A class to handle Notion database operations."""

    def __init__(self, database_id: str):
        """Initialize the Notion client.

        Args:
            database_id: The ID of the target Notion database
        """
        self.database_id = database_id
        self.client = self._create_client()

    def _create_client(self) -> Client:
        """Create and return a Notion client instance."""
        token = os.environ.get("NOTION_TOKEN")
        if not token:
            raise ValueError("NOTION_TOKEN environment variable is not set")
        return Client(auth=token)

    def _truncate_text(self, text: str | None, max_length: int) -> str:
        """Truncate text to max_length and add ellipsis if needed.

        Args:
            text: Text to truncate
            max_length: Maximum length allowed

        Returns:
            Truncated text with ellipsis if needed
        """
        if not text:
            return ""

        if len(text) <= max_length:
            return text

        return text[: max_length - 3] + "..."

    def add_page(
        self,
        title: str | None = None,
        abstract: str | None = None,
        year: int | None = None,
        conf: str | None = None,
        paper_type: str | None = None,
    ) -> Optional[dict[str, Any]]:
        """Add a single page to the Notion database.

        Args:
            title: Paper title
            abstract: Paper abstract (will be truncated to 2000 chars if longer)
            year: Publication year
            conf: Conference name
            type: Type of the paper

        Returns:
            Response from Notion API if successful, None otherwise
        """
        properties = {
            "Name": {
                "title": [{"text": {"content": self._truncate_text(title, 2000)}}]
            },
            "Abstract": {
                "rich_text": [
                    {"text": {"content": self._truncate_text(abstract, 2000)}}
                ]
            },
            "Year": {"number": year},
            "Conf": {"select": {"name": conf}},
        }

        if paper_type:
            properties["Type"] = {"select": {"name": paper_type}}

        page_data = {
            "parent": {"database_id": self.database_id},
            "properties": properties,
        }

        try:
            response = self.client.pages.create(**page_data)
            console.print(f"✅ Added paper: {title}", style="green")
            return response
        except Exception as e:
            console.print(f"❌ Error adding paper '{title}': {str(e)}", style="red")
            return None

    def _load_dataset(self, path: str | Path) -> Iterator[dict[str, Any]]:
        """Load data from a Hugging Face dataset.

        Args:
            path: Path to the dataset directory

        Yields:
            Dictionary containing paper information
        """
        ds = datasets.load_from_disk(path)
        yield from ds

    def _load_jsonl(self, path: str | Path) -> Iterator[dict[str, Any]]:
        """Load data from a JSONL file.

        Args:
            path: Path to the JSONL file

        Yields:
            Dictionary containing paper information
        """
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                yield json.loads(line)

    def import_data(self, file_path: str | Path) -> None:
        """Import papers from either a dataset or JSONL file into Notion.

        Args:
            file_path: Path to the data file or directory
        """
        path = Path(file_path)

        try:
            # Determine the data source type and load accordingly
            if path.is_dir():
                console.print("📂 Loading from dataset directory...", style="blue")
                data_iterator = self._load_dataset(path)
            elif path.suffix == ".jsonl":
                console.print("📄 Loading from JSONL file...", style="blue")
                data_iterator = self._load_jsonl(path)
            else:
                raise ValueError(
                    "Unsupported data source. Please provide either a dataset directory or a .jsonl file"
                )

            # Convert iterator to list to get total count
            items = list(data_iterator)
            items = items[:10]
            total = len(items)
            console.print(f"📚 Found {total} papers to import", style="blue")

            for idx, item in enumerate(items, 1):
                console.print(f"\nProcessing paper {idx}/{total}")
                self.add_page(
                    title=item.get("title"),
                    abstract=item.get("abstract"),
                    year=item.get("year"),
                    conf=item.get("conf"),
                    paper_type=item.get("type"),
                )

        except Exception as e:
            console.print(f"❌ Error loading data: {str(e)}", style="red")
            raise


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Import papers from dataset or JSONL to Notion"
    )
    parser.add_argument("--database_id", required=True, help="Notion database ID")
    parser.add_argument(
        "--input_path",
        required=True,
        help="Path to the dataset directory or JSONL file",
    )

    args = parser.parse_args()

    notion = NotionClient(database_id=args.database_id)
    notion.import_data(args.input_path)


if __name__ == "__main__":
    main()
