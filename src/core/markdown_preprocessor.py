import re


class MarkdownPreprocessor:
    """Preprocess markdown content for parsing."""

    def __init__(self):
        pass

    def preprocess(self, md_content: str) -> str:
        """Preprocess markdown content for better parsing."""
        # Remove HTML comments
        md_content = re.sub(r"<!--.*?-->", "", md_content, flags=re.DOTALL)

        # Normalize line endings
        md_content = md_content.replace("\r\n", "\n")

        # Convert tabs to spaces
        md_content = md_content.replace("\t", "    ")

        # Remove excess whitespace but preserve paragraphs
        md_content = re.sub(r"\n{3,}", "\n\n", md_content)

        return md_content
