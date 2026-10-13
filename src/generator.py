from ollama import chat

from src.quiz import QuizQuestion

MODEL_NAME = "qwen3:4b-instruct"

SYSTEM_PROMPT = """
You are an adaptive active recall learning assistant.

You receive two possible types of knowledge:

PERSONAL_NOTE
Knowledge written by the learner.

EXTERNAL_REFERENCE
Knowledge retrieved from external educational sources.

Your goal is to generate ONE high-quality educational
question.

Rules:

1. Prefer the learner's PERSONAL_NOTE as the primary
   learning context.

2. Use EXTERNAL_REFERENCE to clarify, supplement or
   correct incomplete personal notes.

3. Do not create questions about obscure external facts
   that are unrelated to the learner's concept.

4. If personal and external sources appear to disagree,
   do not silently choose one side.

5. Focus on conceptual understanding rather than trivia.

6. Do not reveal the answer inside the question.

7. The expected answer should explain the concept clearly.

8. concept_ids may contain ONLY IDs from PERSONAL_NOTE
   sources.

9. Never invent a concept ID for an external source.

10. Respect the adaptive question type, difficulty
    and learning focus.

11. If a previous misconception is provided, design
    the question to test that weakness.

Question types:

free_recall:
The learner explains something from memory.

application:
The learner applies knowledge to a scenario.

comparison:
The learner distinguishes or compares concepts.
"""

def generate_question(
    context: str,
    topic: str,

    question_type: str | None = None,
    difficulty: int | None = None,

    focus: str | None = None, 
) -> QuizQuestion:

    requirements = []

    if question_type is not None:
        requirements.append(
            f"""
            QUESTION TYPE: 
            Use this question type: {question_type}
            """
        )    

    if difficulty is not None:
        requirements.append(
            f"""
            DIFFICULTY:
            Use this difficulty level: {difficulty}/5
            """
        )    

    if focus is not None:
        requirements.append(
            f"""
            FOCUS:
            {focus}
            """
        )

    adaptive_requirements = "\n".join(requirements)

    user_prompt = f"""
    The learner wants to practice:
    {topic}

    ADAPTIVE LEARNING REQUIREMENTS:
    {adaptive_requirements}

    Here is the knowledge available to you:


    -- CONTEXT --

    {context}

    -- END CONTEXT -- 

    Generate one active recall question. 

    The question should follow the adaptive learning requirements above.
    
    Do not reveal the expected answer inside the question.
    """

    response = chat(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        format=QuizQuestion.model_json_schema(),

        options={
            "temperature": 0.2,
        }
    )

    question = QuizQuestion.model_validate_json(
        response.message.content
    )

    return question