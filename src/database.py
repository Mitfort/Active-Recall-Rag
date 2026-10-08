import sqlite3
from pathlib import Path

from src.ingestion import ParsedNote

DATABASE_PATH = Path(__file__).parent.parent / "data/learning.db"

def get_connection() -> sqlite3.Connection:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)

    connection.row_factory = sqlite3.Row

    return connection

def initialize_database() -> None:
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS concepts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                note_id INTEGER NOT NULL,
                heading TEXT NOT NULL,
                content TEXT NOT NULL,
                position INTEGER NOT NULL,
                
                FOREIGN KEY (note_id)
                    REFERENCES notes(id)
                    ON DELETE CASCADE
                )
            """)

        connection.commit()

        try:
            connection.execute(
                """
                ALTER TABLE concepts
                ADD COLUMN embedding TEXT
                """
            )
        except sqlite3.OperationalError:
            pass

def get_note_by_file_path(
        connection: sqlite3.Connection,
        file_path: str
    ) -> ParsedNote: 

    return connection.execute(
        """
        SELECT * FROM notes WHERE file_path = ?
        """,
        (file_path,),
    ).fetchone()

def insert_note(
        connection: sqlite3.Connection,
        note: ParsedNote
    ) -> int:
    cursor = connection.execute(
        """
        INSERT INTO notes (file_path, title, content_hash)
        VALUES (?, ?, ?)
        """,
        (
            note.file_path,
            note.title,
            note.content_hash
        ),
    )

    return cursor.lastrowid

def insert_concept(
        connection: sqlite3.Connection,
        note_id: int, 
        note: ParsedNote
    ) -> None:

    for chunk in note.chunks:
        connection.execute(
            """
            INSERT INTO concepts (
                note_id,
                heading,
                content,
                position
            ) VALUES (?, ?, ?, ?)
            """,
            (
                note_id,
                chunk.heading,
                chunk.content,
                chunk.position
            ),
        )

def update_note(
        connection: sqlite3.Connection,
        note_id: int,
        note: ParsedNote
    ) -> None:
    connection.execute(
        """
        UPDATE notes
        SET 
            title = ?, 
            content_hash = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            note.title,
            note.content_hash,
            note_id
        ),
    )

    exsisting_concepts = connection.execute(
        """
        SELECT 
            id,
            heading,
            content
        FROM concepts
        WHERE note_id = ?
        """,
        (note_id,),
    ).fetchall()

    exsisting_by_heading = {
        concept['heading']: concept for concept in exsisting_concepts
    }

    new_headings = set()

    for chunk in note.chunks:
        new_headings.add(chunk.heading)

        existing = exsisting_by_heading.get(
            chunk.heading
        )


        # If the heading does not exist, insert it
        if existing is None:
            connection.execute(
                """
                INSERT INTO concepts (
                    note_id,
                    heading,
                    content,
                    position,
                    embedding
                ) VALUES (?, ?, ?, ?, NULL)
                """,
                (
                    note_id,
                    chunk.heading,
                    chunk.content,
                    chunk.position
                ),
            )

            continue

        # If the heading exists but the content has changed
        if existing['content'] != chunk.content:
            connection.execute(
                """
                UPDATE concepts
                SET 
                    content = ?,
                    position = ?,
                    embedding = NULL 
                WHERE id = ?
                """,
                (
                    chunk.content,
                    chunk.position,
                    existing['id']
                ),
            )
        else:
            # If the heading exists and the content has not changed, just update the position
            connection.execute(
                """
                UPDATE concepts
                SET 
                    position = ?
                WHERE id = ?
                """,
                (
                    chunk.position,
                    existing['id']
                ),
            )

    for heading, existing in exsisting_by_heading.items():
        
        if heading not in new_headings:
            connection.execute(
                """
                DELETE FROM concepts
                WHERE id = ?
                """,
                (existing['id'],)
            )

    # connection.execute(
    #     """
    #     DELETE FROM concepts WHERE note_id = ?
    #     """,
    #     (note_id,),
    # )

    # insert_concept(connection, note_id, note)


def sync_note(note: ParsedNote) -> str:
    with get_connection() as connection:
        existing_note = get_note_by_file_path(connection, note.file_path)

        if existing_note is None:
            note_id = insert_note(connection, note)
            insert_concept(connection, note_id, note)
            connection.commit()
            return "created"

        elif existing_note["content_hash"] == note.content_hash:
            return "unchanged"


        update_note(
            connection,
            existing_note["id"],
            note
        )

        connection.commit()

        return "updated"

def get_all_concepts() -> list[sqlite3.Row]:
    """
    Retrieve all concepts from the database, along with their associated note titles.
        A list of sqlite3.Row objects

    Each row contains the following fields:
        - id: The unique identifier of the concept.
        - note_title: The title of the note associated with the concept.
        - heading: The heading of the concept.
        - content: The content of the concept.
    """

    with get_connection() as connection:

        rows = connection.execute(
            """
            SELECT 
                concepts.id,
                notes.title AS note_title,
                concepts.heading,
                concepts.content
            FROM concepts
            JOIN notes ON concepts.note_id = notes.id
            ORDER BY notes.title, concepts.position
            """
        ).fetchall()

    return rows

def get_concepts_without_embedding() -> list[sqlite3.Row]:
    """
    Retrieve all concepts from the database that do not have an embedding.
        A list of sqlite3.Row objects

    Each row contains the following fields:
        - id: The unique identifier of the concept.
        - note_title: The title of the note associated with the concept.
        - heading: The heading of the concept.
        - content: The content of the concept.
    """

    with get_connection() as connection:

        rows = connection.execute(
           """
            SELECT
                id,
                heading,
                content
            FROM concepts
            WHERE embedding IS NULL
            """
        ).fetchall()

    return rows

def save_embedding(concept_id: int, embedding: list[float]) -> None:
    """
    Save the embedding for a concept in the database.

    Args:
        concept_id (int): The unique identifier of the concept.
        embedding (list[float]): The embedding vector to be saved.
    """

    import json 

    embedding_json = json.dumps(embedding)

    with get_connection() as connection:
        connection.execute(
            """
            UPDATE concepts
            SET embedding = ?
            WHERE id = ?
            """,
            (
                embedding_json,
                concept_id
            )
        )
        connection.commit()

def get_concepts_with_embeddings() -> list[sqlite3.Row]:
    """
    Retrieve all concepts from the database that have an embedding.
        A list of sqlite3.Row objects

    Each row contains the following fields:
        - id: The unique identifier of the concept.
        - note_title: The title of the note associated with the concept.
        - heading: The heading of the concept.
        - content: The content of the concept.
        - embedding: The embedding vector of the concept.
    """

    with get_connection() as connection:

        rows = connection.execute(
            """
            SELECT
                concepts.id,
                concepts.heading,
                concepts.content,
                concepts.embedding,
                notes.title as note_title
            FROM concepts
            JOIN notes ON concepts.note_id = notes.id
            WHERE concepts.embedding IS NOT NULL
            """
        ).fetchall()

    return rows