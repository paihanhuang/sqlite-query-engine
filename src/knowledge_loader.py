"""
Knowledge Loader - Load domain knowledge from Markdown files.

Loads relevant knowledge files based on query keywords to provide
domain-specific context to the LLM.
"""

import re
from pathlib import Path
from typing import Optional


class KnowledgeLoader:
    """Loads and manages domain knowledge from Markdown files."""
    
    def __init__(self, knowledge_dir: str | Path = "knowledge"):
        """
        Initialize the knowledge loader.
        
        Args:
            knowledge_dir: Path to the knowledge directory
        """
        self.knowledge_dir = Path(knowledge_dir)
        self._cache: dict[str, str] = {}
    
    def exists(self) -> bool:
        """Check if knowledge directory exists."""
        return self.knowledge_dir.exists()
    
    def list_files(self) -> list[Path]:
        """List all markdown files in the knowledge directory."""
        if not self.exists():
            return []
        return list(self.knowledge_dir.glob("*.md"))
    
    def load_file(self, filename: str) -> Optional[str]:
        """Load content from a specific knowledge file."""
        filepath = self.knowledge_dir / filename
        if not filepath.exists():
            return None
        
        if filename not in self._cache:
            with open(filepath, 'r', encoding='utf-8') as f:
                self._cache[filename] = f.read()
        
        return self._cache[filename]
    
    def load_all(self) -> dict[str, str]:
        """Load all knowledge files."""
        result = {}
        for filepath in self.list_files():
            content = self.load_file(filepath.name)
            if content:
                result[filepath.name] = content
        return result
    
    def extract_keywords(self, text: str) -> set[str]:
        """Extract keywords from text for matching."""
        # Convert to lowercase and split on non-word characters
        words = re.findall(r'\b[a-z]+\b', text.lower())
        
        # Filter out common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'is', 'are', 'was', 'were',
            'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
            'will', 'would', 'could', 'should', 'may', 'might', 'can', 'to',
            'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from', 'as', 'into',
            'through', 'during', 'before', 'after', 'above', 'below', 'between',
            'under', 'again', 'further', 'then', 'once', 'all', 'each', 'few',
            'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only',
            'own', 'same', 'so', 'than', 'too', 'very', 'just', 'what', 'which',
            'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'show', 'me',
            'list', 'get', 'find', 'give', 'tell', 'how', 'many', 'much', 'when',
            'where', 'why', 'total', 'count', 'sum', 'average', 'avg', 'max', 'min'
        }
        
        return {w for w in words if w not in stop_words and len(w) > 2}
    
    def find_relevant_files(self, query: str, table_names: list[str] = None) -> list[str]:
        """
        Find knowledge files relevant to a query.
        
        Args:
            query: User's natural language question
            table_names: Optional list of table names from schema
            
        Returns:
            List of relevant file names
        """
        if not self.exists():
            return []
        
        query_keywords = self.extract_keywords(query)
        
        # Also include table names as keywords
        if table_names:
            query_keywords.update(t.lower() for t in table_names)
        
        relevant = []
        
        for filepath in self.list_files():
            filename = filepath.name
            file_stem = filepath.stem.lower()
            
            # Check if filename matches any keyword
            if file_stem in query_keywords or any(kw in file_stem for kw in query_keywords):
                relevant.append(filename)
                continue
            
            # Check file content for keyword matches
            content = self.load_file(filename)
            if content:
                content_lower = content.lower()
                matches = sum(1 for kw in query_keywords if kw in content_lower)
                if matches >= 2:  # At least 2 keyword matches
                    relevant.append(filename)
        
        # Always include _joins.md if it exists
        if '_joins.md' in [f.name for f in self.list_files()]:
            if '_joins.md' not in relevant:
                relevant.append('_joins.md')
        
        return relevant
    
    def get_context(self, query: str, table_names: list[str] = None) -> str:
        """
        Get combined knowledge context for a query.
        
        Args:
            query: User's natural language question
            table_names: Optional list of table names from schema
            
        Returns:
            Combined knowledge text for prompt injection
        """
        relevant_files = self.find_relevant_files(query, table_names)
        
        if not relevant_files:
            return ""
        
        sections = ["DOMAIN KNOWLEDGE:", ""]
        
        for filename in relevant_files:
            content = self.load_file(filename)
            if content:
                sections.append(f"### {filename}")
                sections.append(content.strip())
                sections.append("")
        
        return "\n".join(sections)


if __name__ == "__main__":
    # Test
    loader = KnowledgeLoader()
    print(f"Knowledge dir exists: {loader.exists()}")
    print(f"Files: {loader.list_files()}")
    
    # Test keyword extraction
    query = "Show me the total revenue from credit transactions"
    keywords = loader.extract_keywords(query)
    print(f"Keywords: {keywords}")
