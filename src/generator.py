from ollama import chat

from src.quiz import QuizQuestion

MODEL_NAME = "qwen3:4b-instruct"

SYSTEM_PROMPT = """
You are an active recall learning assistant.

Your task is to generate ONE educational question
using ONLY the supplied learning context.

Rules:

1. Do not use outside knowledge.
2. The question must test understanding, not simple recognition.
3. Prefer active recall. 
4. Do not reveal the answer inside the question.
5. The expected answer must be supported by the context.
6. concept_ids must contain only IDs present in the context.
7. Generate a question useful for learning rather than trivia.

Question types:

free_recall:
The learner must explain something from memory.

application:
The learner must apply knowledge to a situation.

comparison:
The learner must compare related concepts.

multiple_choice:
The learner must select the correct answer from a list of options.
""" 

def generate_question(
    context: str,
    topic: str, 
) -> QuizQuestion:

    user_prompt = f"""
    The learner wants to practice:
    {topic}

Here is the learning context:

-- CONTEXT --

{context}

-- END CONTEXT -- 

Generate one active recall question. 
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