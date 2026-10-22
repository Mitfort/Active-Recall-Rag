import json
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from src import database
from src.ingestion import WikiLink, extract_wikilinks, process_note


class WikiLinkTests(unittest.TestCase):
    def test_filters_attachments_and_keeps_note_embeds(self):
        markdown = """
![[Pasted image.png]] ![[photo.JPEG|300]] [[paper.pdf#page=2]]
![[lecture.mp4]] [[data.xlsx]] [[diagram.svg]] ![[sound.mp3]]
[[LinearRegression]] ![[TreeBasedMethods]] [[Folder/Note.md]]
"""

        links = extract_wikilinks(markdown)

        self.assertEqual(
            [link.target for link in links],
            ["LinearRegression", "TreeBasedMethods", "Folder/Note.md"],
        )

    def test_preserves_target_heading_and_alias(self):
        links = extract_wikilinks(
            "[[MachineLearning/LinearRegression#Least squares|Regression]]"
        )

        self.assertEqual(
            links,
            [WikiLink("MachineLearning/LinearRegression", "Least squares", "Regression")],
        )

    def test_ignores_fenced_inline_code_and_hidden_comments(self):
        markdown = """[[Visible]]
```markdown
[[Code example]]
````
~~~
[[Tilde example]]
~~~
`[[Inline example]]` and ``[[Another inline example]]``
<!-- [[HTML comment]] -->
%% [[Obsidian comment]] %%
[[After examples]]
```unclosed
[[Unclosed code]]
"""

        links = extract_wikilinks(markdown)

        self.assertEqual([link.target for link in links], ["Visible", "After examples"])

    def test_resolves_same_note_heading_when_title_is_available(self):
        links = extract_wikilinks(
            "[[#Classification Trees|Classification]]",
            current_note_title="TreeBasedMethods",
        )

        self.assertEqual(
            links,
            [WikiLink("TreeBasedMethods", "Classification Trees", "Classification")],
        )


class NoteSyncTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.directory = Path(self.temporary_directory.name)
        database_patch = patch.object(database, "DATABASE_PATH", self.directory / "test.db")
        database_patch.start()
        self.addCleanup(database_patch.stop)
        self.connections = []
        self.original_get_connection = database.get_connection
        connection_patch = patch.object(database, "get_connection", self.open_connection)
        connection_patch.start()
        self.addCleanup(connection_patch.stop)
        self.addCleanup(self.close_connections)
        database.initialize_database()

    def open_connection(self):
        connection = self.original_get_connection()
        self.connections.append(connection)
        return connection

    def close_connections(self):
        for connection in self.connections:
            connection.close()

    def test_no_h1_uses_file_stem_without_changing_chunk_heading(self):
        note_path = self.directory / "TreeBasedMethods.md"
        note_path.write_text("## Regression Trees\nA tree predicts a value.", encoding="utf-8")

        note = process_note(note_path, fallback_subject="MachineLearning")

        self.assertEqual(note.title, "TreeBasedMethods")
        self.assertEqual(note.chunks[0].heading, "Regression Trees")
        self.assertEqual(note.subject, "MachineLearning")

    def test_explicit_untitled_heading_is_preserved(self):
        note_path = self.directory / "TreeBasedMethods.md"
        note_path.write_text("# Untitled\n## Trees\nContent", encoding="utf-8")

        note = process_note(note_path, fallback_subject="MachineLearning")

        self.assertEqual(note.title, "Untitled")

    def test_unchanged_resync_refreshes_links_and_preserves_learning_records(self):
        note_path = self.directory / "TreeBasedMethods.md"
        note_path.write_text(
            "---\ntags: [machine-learning]\n---\n"
            "## Regression Trees\n"
            "%% Zagadnienie:: Regression Trees %%\n"
            "Related: [[LinearRegression#Least squares|Regression]]\n"
            "![[Pasted image.png]]\n",
            encoding="utf-8",
        )
        note = process_note(note_path, fallback_subject="MachineLearning")
        legacy_note = replace(
            note,
            title="Untitled",
            tags=["legacy"],
            links=[WikiLink("Pasted image.png", None, None)],
        )
        self.assertEqual(database.sync_note(legacy_note), "created")
        with database.get_connection() as connection:
            concept_id = connection.execute("SELECT id FROM concepts").fetchone()["id"]
            connection.execute(
                "UPDATE concepts SET embedding = ? WHERE id = ?",
                (json.dumps([0.1, 0.2]), concept_id),
            )
            connection.execute(
                "INSERT INTO learning_state (concept_id, mastery, review_count) VALUES (?, ?, ?)",
                (concept_id, 0.8, 3),
            )
            connection.execute(
                "INSERT INTO reviews (concept_id, question, expected_answer, rating) "
                "VALUES (?, ?, ?, ?)",
                (concept_id, "Question", "Answer", 4),
            )
            connection.execute(
                "INSERT INTO review_attempts "
                "(concept_id, question, expected_answer, difficulty, question_type, context, sources) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (concept_id, "Question", "Answer", 1, "open", "Context", "[]"),
            )
            before = {
                table: [dict(row) for row in connection.execute(f"SELECT * FROM {table}")]
                for table in ("concepts", "learning_state", "reviews", "review_attempts")
            }

        self.assertEqual(database.sync_note(note), "unchanged")

        with database.get_connection() as connection:
            after = {
                table: [dict(row) for row in connection.execute(f"SELECT * FROM {table}")]
                for table in ("concepts", "learning_state", "reviews", "review_attempts")
            }
            self.assertEqual(after, before)
            stored_note = connection.execute("SELECT * FROM notes").fetchone()
            self.assertEqual(stored_note["title"], "TreeBasedMethods")
            self.assertEqual(stored_note["content_hash"], note.content_hash)
            self.assertEqual(
                [row["tag"] for row in connection.execute("SELECT tag FROM note_tags")],
                ["machine-learning"],
            )
            self.assertEqual(
                [tuple(row) for row in connection.execute(
                    "SELECT target_title, target_heading, alias FROM note_links"
                )],
                [("LinearRegression", "Least squares", "Regression")],
            )


if __name__ == "__main__":
    unittest.main()
