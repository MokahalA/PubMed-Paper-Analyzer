import json
import sqlite3
from typing import Optional, List
from .schema import init_db, get_connection


class PaperRepository:
    """Repository for managing papers in SQLite database."""

    def __init__(self):
        """Initialize and ensure database schema exists."""
        init_db()

    def insert_or_update(self, paper: dict) -> bool:
        """
        Insert or update a paper using PMID as primary key.
        This prevents duplicates automatically.

        Args:
            paper: Cleaned paper dict with required fields

        Returns:
            True if inserted/updated, False if failed
        """
        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
            INSERT INTO papers (
                pmid, title, abstract, authors, journal, year,
                keywords, diseases, methods, organs, clean_text,
                abstract_words, title_words
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(pmid) DO UPDATE SET
                title = excluded.title,
                abstract = excluded.abstract,
                authors = excluded.authors,
                journal = excluded.journal,
                year = excluded.year,
                keywords = excluded.keywords,
                diseases = excluded.diseases,
                methods = excluded.methods,
                organs = excluded.organs,
                clean_text = excluded.clean_text,
                abstract_words = excluded.abstract_words,
                title_words = excluded.title_words,
                updated_at = CURRENT_TIMESTAMP
            """, (
                paper.get("pmid"),
                paper.get("title", ""),
                paper.get("abstract", ""),
                json.dumps(paper.get("authors", [])),
                paper.get("journal", ""),
                paper.get("year"),
                json.dumps(paper.get("keywords", [])),
                json.dumps(paper.get("entities", {}).get("diseases", [])),
                json.dumps(paper.get("entities", {}).get("methods", [])),
                json.dumps(paper.get("entities", {}).get("organs", [])),
                paper.get("clean_text", ""),
                paper.get("length", {}).get("abstract_words", 0),
                paper.get("length", {}).get("title_words", 0)
            ))

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            print(f"Error inserting paper {paper.get('pmid')}: {e}")
            return False

    def insert_batch(self, papers: list[dict]) -> dict:
        """
        Insert multiple papers into database.

        Args:
            papers: List of cleaned paper dicts

        Returns:
            Dict with statistics: {inserted: int, updated: int, failed: int}
        """
        stats = {"inserted": 0, "updated": 0, "failed": 0}

        for paper in papers:
            try:
                # Check if already exists
                existing = self.get_by_pmid(paper.get("pmid"))

                if self.insert_or_update(paper):
                    if existing:
                        stats["updated"] += 1
                    else:
                        stats["inserted"] += 1
                else:
                    stats["failed"] += 1
            except Exception as e:
                print(f"Error processing paper: {e}")
                stats["failed"] += 1

        return stats

    def get_by_pmid(self, pmid: str) -> Optional[dict]:
        """Get a single paper by PMID."""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM papers WHERE pmid = ?", (pmid,))
            row = cursor.fetchone()
            conn.close()

            if row:
                return self._row_to_dict(row, cursor.description)
            return None
        except Exception as e:
            print(f"Error fetching paper: {e}")
            return None

    def get_all(self, limit: int = None) -> List[dict]:
        """Get all papers from database."""
        try:
            conn = get_connection()
            cursor = conn.cursor()

            query = "SELECT * FROM papers ORDER BY created_at DESC"
            if limit:
                query += f" LIMIT {limit}"

            cursor.execute(query)
            rows = cursor.fetchall()
            conn.close()

            return [self._row_to_dict(row, cursor.description) for row in rows]
        except Exception as e:
            print(f"Error fetching papers: {e}")
            return []

    def get_by_year(self, year: int) -> List[dict]:
        """Get papers from a specific year."""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM papers WHERE year = ? ORDER BY created_at DESC", (year,))
            rows = cursor.fetchall()
            conn.close()

            return [self._row_to_dict(row, cursor.description) for row in rows]
        except Exception as e:
            print(f"Error fetching papers by year: {e}")
            return []

    def search_by_keyword(self, keyword: str) -> List[dict]:
        """Search papers by keyword in title or clean_text."""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            keyword_lower = keyword.lower()

            cursor.execute("""
            SELECT * FROM papers 
            WHERE LOWER(title) LIKE ? OR LOWER(clean_text) LIKE ?
            ORDER BY created_at DESC
            """, (f"%{keyword_lower}%", f"%{keyword_lower}%"))

            rows = cursor.fetchall()
            conn.close()

            return [self._row_to_dict(row, cursor.description) for row in rows]
        except Exception as e:
            print(f"Error searching papers: {e}")
            return []

    def count(self) -> int:
        """Get total number of papers in database."""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM papers")
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception as e:
            print(f"Error counting papers: {e}")
            return 0

    def delete_by_pmid(self, pmid: str) -> bool:
        """Delete a paper by PMID."""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM papers WHERE pmid = ?", (pmid,))
            conn.commit()
            conn.close()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error deleting paper: {e}")
            return False

    def clear_all(self) -> bool:
        """Delete all papers from database."""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM papers")
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error clearing database: {e}")
            return False

    def get_recent(self, limit: int = 10) -> List[tuple]:
        """Get most recently added papers as raw tuples."""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM papers ORDER BY created_at DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            conn.close()
            return rows
        except Exception as e:
            print(f"Error fetching recent papers: {e}")
            return []

    @staticmethod
    def _row_to_dict(row: tuple, description) -> dict:
        """Convert database row to dictionary."""
        paper = {}
        for i, col in enumerate(description):
            col_name = col[0]
            value = row[i]

            # Parse JSON fields
            if col_name in ["authors", "keywords", "diseases", "methods", "organs"]:
                paper[col_name] = json.loads(value) if value else []
            else:
                paper[col_name] = value

        return paper
