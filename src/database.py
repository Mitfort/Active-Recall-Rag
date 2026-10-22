import sqlite3
from pathlib import Path

from src.ingestion import ParsedNote

from datetime import datetime, date

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
                subject TEXT NOT NULL DEFAULT 'General',
                metadata_json TEXT,
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

        connection.execute("""
            CREATE TABLE IF NOT EXISTS review_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                
                concept_id INTEGER NOT NULL,
                
                question TEXT NOT NULL,
                expected_answer TEXT NOT NULL,

                difficulty INTEGER NOT NULL,
                question_type TEXT NOT NULL,

                context TEXT NOT NULL,

                sources TEXT NOT NULL,

                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

                completed_at DATETIME,

                FOREIGN KEY (concept_id)
                    REFERENCES concepts(id)
                    ON DELETE CASCADE
                )
            """
        )

        connection.execute("""
            CREATE TABLE IF NOT EXISTS note_tags (
                note_id INTEGER NOT NULL,
                
                tag TEXT NOT NULL,
                
                PRIMARY KEY (note_id, tag),
                
                FOREIGN KEY (note_id)
                    REFERENCES notes(id)
                    ON DELETE CASCADE
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS note_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                
                source_note_id INTEGER NOT NULL,
                target_title TEXT NOT NULL,
                
                target_heading TEXT,
                
                alias TEXT,
                
                FOREIGN KEY (source_note_id)
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

        try:
            connection.execute(
                """
                ALTER TABLE reviews
                ADD COLUMN source_provenance TEXT
                """
            )
        except sqlite3.OperationalError:
            pass

        try:
            connection.execute(
                """
                ALTER TABLE notes
                ADD COLUMN subject TEXT NOT NULL DEFAULT 'General'
                """
            )
        except sqlite3.OperationalError:
            pass

        try:
            connection.execute(
                """
                ALTER TABLE notes
                ADD COLUMN metadata_json TEXT
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
    def _serialize_metadata(obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, dict):
            return {k: _serialize_metadata(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_serialize_metadata(v) for v in obj]
        return obj

    cursor = connection.execute(
        """
        INSERT INTO notes (
            file_path,
            title,
            subject, 
            metadata_json, 
            content_hash
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            note.file_path,
            note.title,
            note.subject,
            json.dumps(_serialize_metadata(note.metadata), ensure_ascii=False),
            note.content_hash
        ),
    )

    note_id = cursor.lastrowid

    sync_note_metadata(
        connection,
        note_id,
        note
    )

    return note_id

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
    
    def _serialize_metadata(obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, dict):
            return {k: _serialize_metadata(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_serialize_metadata(v) for v in obj]
        return obj

    connection.execute(
        """
        UPDATE notes
        SET 
            title = ?, 
            subject = ?,
            metadata_json = ?,
            content_hash = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            note.title,
            note.subject,
            json.dumps(_serialize_metadata(note.metadata), ensure_ascii=False),
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

    sync_note_metadata(
        connection,
        note_id,
        note
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
            # Parser improvements must reach existing notes without rebuilding concepts.
            connection.execute(
                "UPDATE notes SET title = ?, subject = ? WHERE id = ?",
                (note.title, note.subject, existing_note["id"]),
            )
            sync_note_metadata(connection, existing_note["id"], note)
            connection.commit()
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
    combined_score:float | None = None,

    source_provenance: list[dict] | None = None
) -> None:

    ensure_learning_state(concept_id)

    missing_points_json = json.dumps(missing_points or []) 
    missconceptions_json = json.dumps(misconceptions or [])
    source_provenance_json = json.dumps(source_provenance or [])

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
                combined_score,

                source_provenance
            ) VALUES (?, ?, ?, ?, ?, 
                      ?, ?, ?, ?, 
                      ?, ?, ? )
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
                combined_score,

                source_provenance_json
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

                COALESCE (
                    learning_state.stability_days,
                    1.0
                ) AS stability_days,

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
                notes.title AS note
            FROM concepts

            JOIN notes ON notes.id = concepts.note_id

            WHERE concepts.id = ?
            """,
            (concept_id,)
        ).fetchone()

def get_recent_reviews(
        concept_id: int,
        limit: int = 5
) -> list[sqlite3.Row]:

    with get_connection() as connection:
        return connection.execute(
            """
            SELECT 
                id,
                question,
                user_answer,
                rating,
                
                ai_correctness,

                missing_points,
                misconceptions,

                user_confidence,
                combined_score,
                reviewed_at

            FROM reviews
            WHERE concept_id = ?
            ORDER BY reviewed_at DESC
            LIMIT ?
            """,
            (concept_id, limit)
        ).fetchall()

def get_all_concepts_with_state() -> list[sqlite3.Row]:
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT
                concepts.id,
                concepts.heading,
                concepts.content,

                notes.title AS note,

                COALESCE(learning_state.mastery, 0.0) AS mastery,

                COALESCE(learning_state.stability_days, 1.0) AS stability_days,

                COALESCE(learning_state.review_count, 0) AS review_count,

                learning_state.last_reviewed,
                learning_state.next_review
            FROM concepts

            JOIN notes ON notes.id = concepts.note_id
            LEFT JOIN learning_state ON learning_state.concept_id = concepts.id

            ORDER BY
                notes.title,
                concepts.position
            
            """).fetchall()

def get_review(
        review_id: int
) -> sqlite3.Row:

    with get_connection() as connection:
        return connection.execute(
            """
            SELECT * 
            FROM reviews
            WHERE id = ? 
            """,
            (review_id)
        ).fetchone()

def create_review_attempt(
    concept_id: int,
    question: str,
    expected_answer: str,
    difficulty: int,
    question_type: str,
    context: str,
    sources: list[dict]
) -> int:
    import json 

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO review_attempts (
                concept_id,
                question,
                expected_answer,
                difficulty,
                question_type,
                context,
                sources
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                concept_id,
                question,
                expected_answer,
                difficulty,
                question_type,
                context,
                json.dumps(sources)
            )
        )

        connection.commit()

        return cursor.lastrowid


def get_review_attempt(
    attempt_id: int
) -> sqlite3.Row:

    with get_connection() as connection:
        return connection.execute(
            """
            SELECT * 
            FROM review_attempts
            WHERE id = ?
            AND completed_at IS NULL
            """,
            (attempt_id,)
        ).fetchone()

def complete_review_attempt(
    attempt_id: int
) -> None:

    with get_connection() as connection:
        connection.execute(
            """
            UPDATE review_attempts
            SET completed_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (attempt_id,)
        )

        connection.commit()

def count_due_concepts() -> int:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM concepts
            LEFT JOIN learning_state ON learning_state.concept_id = concepts.id
            WHERE 
                learning_state.next_review IS NULL
                OR datetime(learning_state.next_review) <= datetime('now')
            """
        ).fetchone()

    return row['count']

def get_recent_review_stats(
    days: int = 7
):
    modifier: str = f"-{days} days"

    with get_connection() as connection:
        return connection.execute(
            """
            SELECT
                COUNT(*) AS review_count,
                AVG(ai_correctness) AS average_correctness,
                AVG(combined_score) AS average_score
            FROM reviews
            WHERE datetime(reviewed_at) >= datetime('now', ?)""",
            (modifier,)
        ).fetchone()

def get_review_history(
        limit:int = 50,
        offset:int = 0
):
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT
                reviews.id,
                reviews.concept_id,
                
                concepts.heading,
                notes.title AS note,
                
                reviews.question,
                reviews.user_answer,
                
                reviews.ai_correctness,
                reviews.ai_feedback,
                
                reviews.user_confidence,
                reviews.combined_score,
                
                reviews.rating,
                
                reviews.reviewed_at
            FROM reviews
            
            JOIN concepts ON concepts.id = reviews.concept_id
            JOIN notes ON notes.id = concepts.note_id
            
            ORDER BY reviews.reviewed_at DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset)
        ).fetchall()

def get_review_activity(
    days:int = 7
):
    modifier: str = f"-{days} days"

    with get_connection() as connection:
        return connection.execute(
            """
            SELECT
                date(reviewed_at) AS day,
                COUNT(*) AS reviews,
                AVG(ai_correctness) AS average_correctness
            FROM reviews
            WHERE datetime(reviewed_at) >= datetime('now', ?)
            GROUP BY date(reviewed_at)
            ORDER BY day ASC
            """,
            (modifier,)
        ).fetchall()  


def get_knowledge_rows():
    with get_connection() as connection:
        return connection.execute(
        """
        SELECT 
            concepts.id,
            concepts.heading,
            concepts.content,

            notes.id AS note_id,
            notes.title as note,
            notes.subject as subject,

            COALESCE(learning_state.mastery, 0.0) AS mastery,
            COALESCE(learning_state.stability_days, 1.0) AS stability_days,
            COALESCE(learning_state.review_count, 0) AS review_count,

            learning_state.last_reviewed,
            learning_state.next_review
        FROM concepts
        JOIN notes ON notes.id = concepts.note_id
        LEFT JOIN learning_state ON learning_state.concept_id = concepts.id

        ORDER BY 
            notes.subject,
            notes.title,
            concepts.position
        """   
        ).fetchall()

def sync_note_metadata(
    connection: sqlite3.Connection,
    note_id: int,
    note: ParsedNote
) -> None:

    ### TAGS 

    connection.execute(
        """
        DELETE FROM note_tags
        WHERE note_id = ?
        """,
        (note_id,)
    )

    for tag in note.tags:
        connection.execute(
            """
            INSERT INTO note_tags (note_id, tag)
            VALUES (?, ?)
            """,
            (note_id, tag)
        )

    ### WIKILINKS

    connection.execute(
        """
        DELETE FROM note_links
        WHERE source_note_id = ?
        """,
        (note_id,)
    )

    for link in note.links:
        connection.execute(
            """
            INSERT INTO note_links (
                source_note_id,
                target_title,
                target_heading,
                alias
            ) VALUES (?, ?, ?, ?)
            """,
            (
                note_id,
                link.target,
                link.heading,
                link.alias
            )
        )

def get_note_metadata(note_id: int):
    with get_connection() as connection:

        note = connection.execute(
            """
            SELECT 
                notes.id,
                notes.title,
                notes.subject,
                notes.file_path,
                notes.metadata_json
            FROM notes
            WHERE notes.id = ?
            """,
            (note_id,)
        ).fetchone()

        if note is None:
            return None

        tags = connection.execute(
            """
            SELECT tag
            FROM note_tags
            WHERE note_id = ?
            ORDER BY tag
            """,
            (note_id,)
        ).fetchall()

        links = connection.execute(
            """
            SELECT 
                target_title,
                target_heading,
                alias
            FROM note_links
            WHERE source_note_id = ?
            ORDER BY target_title
            """,
            (note_id,)
        ).fetchall()

        return {
            "id": note["id"],
            "title": note["title"],
            "subject": note["subject"],
            "file_path": note["file_path"],
            "metadata": json.loads(note["metadata_json"]) if note["metadata_json"] else {},
            "tags": [tag["tag"] for tag in tags],
            "links": [
                {
                    "target": row["target_title"],
                    "heading": row["target_heading"],
                    "alias": row["alias"]
                }

                for row in links
            ],
        }

def get_knowledge_graph():
    with get_connection() as connection:

        notes = connection.execute(
            """
            SELECT 
                id,
                title,
                subject,
                file_path,
                metadata_json
            FROM notes
            """
        ).fetchall()

        links = connection.execute(
            """
            SELECT 
                source_note_id,
                target_title,
                target_heading
            FROM note_links
            """
        ).fetchall()

    return notes, links

def get_note_embedding_rows():
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT
                notes.id AS note_id,
                notes.title AS note_title,
                notes.subject,

                concepts.id AS concept_id,
                concepts.heading,
                concepts.embedding    
            
            FROM notes

            JOIN concepts ON concepts.note_id = notes.id

            WHERE concepts.embedding IS NOT NULL

            ORDER BY
                notes.subject,
                concepts.position
            """
        ).fetchall()
