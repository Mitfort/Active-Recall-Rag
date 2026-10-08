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