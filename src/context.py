from src.external_knowledge import ExternalSource

def build_context(
        retrueval_results: list[dict]
) -> str: 

    parts = []

    for result in retrueval_results:
        part = f"""
        CONCEPT_ID {result['id']}
        NOTE: {result['note']}
        CONCEPT: {result['heading']}

        CONTENT: {result['content']}
        """.strip()
        parts.append(part)

    return "\n\n---\n\n".join(parts)

def build_enriched_context(
    personal_results: list[dict],
    external_sources: list[ExternalSource]
) -> str: 
    parts = []

    ## PERSONAL KNOWLEDGE
    for result in personal_results:
        part = f"""
SOURCE_TYPE: PERSONAL_NOTE

CONCEPT_ID: {result["id"]}
NOTE: {result["note"]}
CONCEPT: {result["heading"]}

CONTENT:
{result["content"]}
""".strip()

        parts.append(part)

    ## EXTERNAL SOURCES

    for source in external_sources:
        part = f"""
SOURCE_TYPE: EXTERNAL_REFERENCE

PROVIDER: {source.provider}
TITLE: {source.title}
URL: {source.url}

CONTENT:
{source.content}
""".strip()

        parts.append(part)

    return "\n\n---\n\n".join(parts)