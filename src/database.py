import sqlite3
from pathlib import Path

from src.ingestion import ParsedNote

from datetime import datetime

import json 

DATABASE_PATH = Path(__file__).parent.parent / "data/learning.db"

def get_connection() -> sqlite3.Connection:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)

    connection.row_factory = sqlite3.Row

    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

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

        connection.execute("""
            CREATE TABLE IF NOT EXISTS learning_state (
                concept_id INTEGER PRIMARY KEY,
                mastery REAL NOT NULL DEFAULT 0.0,
                
                review_count INTEGER NOT NULL DEFAULT 0,
                correct_count INTEGER NOT NULL DEFAULT 0,
                
                last_reviewed DATETIME,
                next_review DATETIME,
                
                FOREIGN KEY (concept_id)
                    REFERENCES concepts(id)
                    ON DELETE CASCADE
                )
            """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                concept_id INTEGER NOT NULL,
                
                question TEXT NOT NULL,
                expected_answer TEXT NOT NULL,
                
                user_answer TEXT,
                rating INTEGER NOT NULL,

                reviewed_at DATETIME DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (concept_id)
                    REFERENCES concepts(id)
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

        columns = [
            (
                "ai_correctness",
                "REAL"
            ),
            (
                "ai_feedback",
                "TEXT"
            ),
            (
                "missing_points",
                "TEXT"
            ),
            (
                "misconceptions",
                "TEXT"
            ),
            (
                "user_confidence",
                "INTEGER"
            ),
            (
                "combined_score",
                "REAL"
            ),
        ]

        for column_name, column_type in columns:
            try:
                connection.execute(
                    f"""
                    ALTER TABLE reviews
                    ADD COLUMN {column_name} {column_type}
                    """
                )
            except sqlite3.OperationalError:
                pass

        try:
            connection.execute(
                """
                ALTER TABLE learning_state
                ADD COLUMN stability_days REAL NOT NULL DEFAULT 1.0
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

def ensure_learning_state(concept_id: int) -> None:
    """
    Ensure that a learning state entry exists for the given concept ID.
    If it does not exist, create a new entry with default values.

    Args:
        concept_id (int): The unique identifier of the concept.
    """

    with get_connection() as connection:

        connection.execute(
            """
            INSERT OR IGNORE INTO learning_state (concept_id)
            VALUES (?)
            """,
            (concept_id,)
        )

        connection.commit()

def get_learning_state(concept_id: int) -> sqlite3.Row:

    ensure_learning_state(concept_id)

    with get_connection() as connection:

        return connection.execute(
            """
            SELECT * FROM learning_state
            WHERE concept_id = ?
            """,
            (concept_id,)
        ).fetchone()

def save_review(
    concept_id: int,
    question: str,
    expected_answer: str,
    user_answer: str,
    rating: int,
    
    new_mastery: float,
    next_review: datetime,
    new_stability: float,

    ai_correctness:float | None = None,
    ai_feedback:str | None = None,

    missing_points:list[str] | None = None,
    misconceptions:list[str] | None = None,

    user_confidence:int | None = None,
    combined_score:float | None = None
) -> None:

    ensure_learning_state(concept_id)

    missing_points_json = json.dumps(missing_points or []) 
    missconceptions_json = json.dumps(misconceptions or [])

    with get_connection() as connection:

        connection.execute(
            """
            INSERT INTO reviews (
                concept_id,
                question,
                expected_answer,
                user_answer,
                rating,

                ai_correctness,
                ai_feedback,
                missing_points,
                misconceptions,

                user_confidence,
                combined_score
            ) VALUES (?, ?, ?, ?, ?, 
                      ?, ?, ?, ?, 
                      ?, ?)
            """,
            (
                concept_id,
                question,
                expected_answer,
                user_answer,
                rating,

                ai_correctness,
                ai_feedback,
                missing_points_json,
                missconceptions_json,

                user_confidence,
                combined_score
            )
        )

        correct_increment = (
            1 if rating >= 3 else 0
        )

        connection.execute(
            """
            UPDATE learning_state
            
            SET 
                mastery = ?,
                stability_days = ?,
                review_count = review_count + 1,
                correct_count = correct_count + ?,
                last_reviewed = CURRENT_TIMESTAMP,
                next_review = ?
            WHERE concept_id = ?
            """,
            (
                new_mastery,
                new_stability,
                correct_increment,
                next_review.isoformat(),
                concept_id
            )
        )

        connection.commit()

def get_all_learning_states() -> list[sqlite3.Row]:
    """
    Retrieve all learning states from the database.
        A list of sqlite3.Row objects

    Each row contains the following fields:
        - concept_id: The unique identifier of the concept.
        - mastery: The current mastery level of the concept.
        - review_count: The total number of reviews for the concept.
        - correct_count: The total number of correct reviews for the concept.
        - last_reviewed: The timestamp of the last review for the concept.
        - next_review: The timestamp of the next scheduled review for the concept.
    """

    with get_connection() as connection:

        rows = connection.execute(
            """
            SELECT 
                concepts.id,
                notes.title AS note,
                concepts.heading,
                learning_state.mastery,
                learning_state.stability_days,
                learning_state.review_count,
                learning_state.correct_count,
                learning_state.last_reviewed,
                learning_state.next_review
            FROM learning_state

            JOIN concepts ON learning_state.concept_id = concepts.id
            JOIN notes ON notes.id = concepts.note_id

            ORDER BY 
                learning_state.mastery ASC
            """
        ).fetchall()

    return rows

def get_daily_review_concepts(
        limit: int = 10 
):
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT 
                concepts.id,
                concepts.heading,
                concepts.content,
                notes.title AS note,

                COALESCE (
                    learning_state.mastery,
                    0.0
                ) AS mastery,

                COALESCE (
                    learning_state.review_count,
                    0
                ) AS review_count,

                learning_state.last_reviewed,
                learning_state.next_review

            FROM concepts

            JOIN notes ON notes.id = concepts.note_id

            LEFT JOIN learning_state ON learning_state.concept_id = concepts.id
        
            WHERE 
                learning_state.next_review IS NULL
                OR datetime(learning_state.next_review) <= datetime('now')

            ORDER BY
                CASE 
                    WHEN learning_state.next_review IS NULL
                    THEN 0
                    ELSE 1
                END,

                mastery ASC,
                learning_state.next_review ASC
            LIMIT ? 
            """,
            (limit,),
        ).fetchall()

def get_concept(concept_id: int) -> sqlite3.Row:
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT 
                concepts.id,
                concepts.heading,
                concepts.content,
                notes.title AS note,
            FROM concepts

            JOIN notes ON notes.id = concepts.note_id

            WHERE concepts.id = ?
            """,
            (concept_id,)
        ).fetchone()