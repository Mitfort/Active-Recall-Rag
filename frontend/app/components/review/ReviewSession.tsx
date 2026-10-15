"use client";

import {
    useState,
} from "react";

import Link from "next/link";

import {
    createQuestion,
    submitAnswer
} from "@/app/lib/api"

import type {
    AnswerResult,
    ReviewConcept,
    ReviewQuestion
} from "@/app/types/api"

import {
    ReviewResult,
} from "@/app/components/review/ReviewResult";

type Props = {
    concepts: ReviewConcept[];
}

export function ReviewSession({
    concepts
}: Props) {

    const [currentIndex,setCurrentIndex] = useState(0);
    const [question,setQuestion] = useState<ReviewQuestion | null>(null);
    const [answer,setAnswer] = useState("");
    const [confidence,setConfidence] = useState<number | null>(null);
    const [result,setResult] = useState<AnswerResult | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    if (concepts.length === 0) {

    return (
      <div
        className="
          rounded-3xl
          border border-zinc-800
          bg-zinc-900
          p-10
          text-center
        "
      >
        <h1
          className="
            text-3xl
            font-semibold
          "
        >
          You're caught up 🎉
        </h1>

        <p
          className="
            mt-3
            text-zinc-400
          "
        >
          There are no concepts due
          for review today.
        </p>

        <Link
          href="/"
          className="
            mt-8
            inline-flex
            rounded-xl
            bg-zinc-100
            px-6
            py-3
            font-medium
            text-zinc-950
          "
        >
          Back to dashboard
        </Link>
      </div>
    );
  }


  const concept =
    concepts[currentIndex];


  const progress =
    (
      currentIndex
      / concepts.length
    ) * 100;


  async function handleGenerateQuestion() {

    setLoading(true);
    setError(null);

    try {

      const generated =
        await createQuestion(
          concept.id
        );

      setQuestion(
        generated
      );

    } catch {

      setError(
        "Could not generate the question."
      );

    } finally {

      setLoading(false);

    }
  }


  async function handleSubmit() {

    if (
      !question
      || !answer.trim()
      || confidence === null
    ) {
      return;
    }

    setLoading(true);
    setError(null);

    try {

      const evaluation =
        await submitAnswer(
          question.attempt_id,
          answer,
          confidence,
        );

      setResult(
        evaluation
      );

    } catch {

      setError(
        "Could not evaluate your answer."
      );

    } finally {

      setLoading(false);

    }
  }


  function handleNext() {

    const nextIndex =
      currentIndex + 1;

    if (
      nextIndex >=
      concepts.length
    ) {

      setCurrentIndex(
        concepts.length
      );

      return;
    }

    setCurrentIndex(
      nextIndex
    );

    setQuestion(null);

    setAnswer("");

    setConfidence(null);

    setResult(null);

    setError(null);
  }


  if (
    currentIndex
    >= concepts.length
  ) {

    return (
      <div
        className="
          rounded-3xl
          border border-zinc-800
          bg-zinc-900
          p-10
          text-center
        "
      >

        <p
          className="
            text-sm
            text-zinc-500
          "
        >
          Daily review complete
        </p>

        <h1
          className="
            mt-3
            text-4xl
            font-semibold
          "
        >
          Session complete 🎉
        </h1>

        <p
          className="
            mt-4
            text-zinc-400
          "
        >
          You reviewed{" "}
          {concepts.length} concepts.
        </p>

        <Link
          href="/"
          className="
            mt-8
            inline-flex
            rounded-xl
            bg-zinc-100
            px-6
            py-3
            font-medium
            text-zinc-950
          "
        >
          Return to dashboard
        </Link>

      </div>
    );
  }


  return (
    <div>

      {/* Progress */}

      <div
        className="
          mb-8
        "
      >
        <div
          className="
            flex
            items-center
            justify-between
            text-sm
          "
        >
          <span
            className="
              text-zinc-500
            "
          >
            Daily review
          </span>

          <span
            className="
              text-zinc-400
            "
          >
            {currentIndex + 1}
            {" / "}
            {concepts.length}
          </span>
        </div>


        <div
          className="
            mt-3
            h-1.5
            overflow-hidden
            rounded-full
            bg-zinc-800
          "
        >
          <div
            className="
              h-full
              bg-zinc-100
              transition-all
              duration-500
            "
            style={{
              width:
                `${progress}%`,
            }}
          />
        </div>

      </div>


      {/* Concept */}

      <div
        className="
          mb-4
        "
      >
        <p
          className="
            text-sm
            text-zinc-500
          "
        >
          {concept.note}
        </p>

        <h1
          className="
            mt-1
            text-2xl
            font-semibold
          "
        >
          {concept.heading}
        </h1>
      </div>


      {!question && (

        <div
          className="
            rounded-3xl
            border border-zinc-800
            bg-zinc-900
            p-8
          "
        >

          <p
            className="
              text-zinc-400
            "
          >
            The learning engine will generate
            an adaptive question based on your
            previous performance and memory state.
          </p>


          <button
            onClick={
              handleGenerateQuestion
            }
            disabled={loading}
            className="
              mt-6
              rounded-xl
              bg-zinc-100
              px-6
              py-3
              font-medium
              text-zinc-950
              disabled:opacity-50
            "
          >
            {loading
              ? "Generating..."
              : "Generate question"}
          </button>

        </div>

      )}


      {question && !result && (

        <div
          className="
            rounded-3xl
            border border-zinc-800
            bg-zinc-900
            p-8
          "
        >

          <div
            className="
              flex
              gap-2
              text-xs
            "
          >
            <span
              className="
                rounded-full
                bg-zinc-800
                px-3
                py-1
                text-zinc-400
              "
            >
              {question.question_type}
            </span>

            <span
              className="
                rounded-full
                bg-zinc-800
                px-3
                py-1
                text-zinc-400
              "
            >
              Difficulty{" "}
              {question.difficulty}/5
            </span>
          </div>


          <h2
            className="
              mt-6
              text-xl
              font-medium
              leading-relaxed
            "
          >
            {question.question}
          </h2>


          <textarea
            value={answer}

            onChange={(event) =>
              setAnswer(
                event.target.value
              )
            }

            placeholder={
              "Answer from memory..."
            }

            rows={7}

            className="
              mt-8
              w-full
              resize-none
              rounded-2xl
              border border-zinc-700
              bg-zinc-950
              p-4
              text-zinc-100
              outline-none
              transition
              focus:border-zinc-500
            "
          />


          <div className="mt-6">

            <p
              className="
                text-sm
                text-zinc-400
              "
            >
              How confident are you?
            </p>


            <div
              className="
                mt-3
                grid
                grid-cols-4
                gap-2
              "
            >

              {[
                {
                  value: 1,
                  label: "Guess",
                },
                {
                  value: 2,
                  label: "Unsure",
                },
                {
                  value: 3,
                  label: "Confident",
                },
                {
                  value: 4,
                  label: "Certain",
                },
              ].map((item) => (

                <button
                  key={item.value}

                  onClick={() =>
                    setConfidence(
                      item.value
                    )
                  }

                  className={`
                    rounded-xl
                    border
                    px-3
                    py-3
                    text-sm
                    transition

                    ${
                      confidence
                      === item.value

                        ? `
                          border-zinc-200
                          bg-zinc-200
                          text-zinc-950
                        `

                        : `
                          border-zinc-700
                          bg-zinc-950
                          text-zinc-400
                          hover:border-zinc-500
                        `
                    }
                  `}
                >
                  {item.label}
                </button>

              ))}

            </div>

          </div>


          <button
            onClick={handleSubmit}

            disabled={
              loading
              || !answer.trim()
              || confidence === null
            }

            className="
              mt-8
              w-full
              rounded-xl
              bg-zinc-100
              px-6
              py-3
              font-medium
              text-zinc-950
              disabled:opacity-40
            "
          >
            {loading
              ? "Evaluating..."
              : "Submit answer"}
          </button>

        </div>

      )}


      {result && (

        <ReviewResult
          result={result}
          onNext={handleNext}
        />

      )}


      {error && (

        <p
          className="
            mt-4
            text-sm
            text-red-400
          "
        >
          {error}
        </p>

      )}

    </div>
  );
}