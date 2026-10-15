"use client";

import type {
    AnswerResult
} from "@/app/types/api";

type Props = {
    result: AnswerResult;

    onNext: () => void;
}

export function ReviewResult({
    result,
    onNext
}: Props) {

    const correctness = Math.round(result.correctness * 100);
    const masteryBefore = Math.round(result.mastery_before * 100);
    const masteryAfter = Math.round(result.mastery_after * 100);
    
    return (
        <div className="
            rounded-3xl
            border border-zinc-800
            bg-zinc-900
            p-8
        ">
            <p className="
                text-sm
                text-zinc-500"
            >
                AI evaluation
            </p>

            <div className="
                mt-3
                flex
                items-baseline
                gap-3"
            >
                <span className="
                    text-5xl
                    font-semibold
                ">
                    {correctness}%
                </span>

                <span className="
                    text-zinc-400
                ">
                    {result.verdict}
                </span>

            </div>

            <p className="
                mt-6
                leading-relaxed
                text-zinc-300
            ">
                {result.feedback}
            </p>

            {result.missing_points.length > 0 && (
                <div className="mt-8">
                    <h3
                        className="
                        font-medium
                        text-zinc-200
                        "
                    >
                        Missing points
                    </h3>

                    <ul
                        className="
                        mt-3
                        space-y-2
                        text-sm
                        text-zinc-400
                        "
                    >
                        {result.missing_points.map(
                        (point) => (

                            <li key={point}>
                            • {point}
                            </li>

                        )
                        )}
                    </ul>

                </div>

            )}

            {result.missconceptions.length > 0 && (
                <div className="mt-8">
                    <h3
                        className="
                        font-medium
                        text-zinc-200
                    ">
                        Misconceptions
                    </h3>

                    <ul className="
                        mt-3
                        space-y-2
                        text-sm
                        text-zinc-400
                    ">
                        {result.missconceptions.map(
                        (point) => (
                            <li key={point}>
                            • {point}
                            </li>
                        )
                        )}
                    </ul>

                </div>

            )}

            {result.missconceptions.length > 0 && (
                <div className="mt-8">
                    <h3
                        className="
                        font-medium
                        text-zinc-200
                    ">
                        Misconceptions
                    </h3>

                    <ul className="
                        mt-3
                        space-y-2
                        text-sm
                        text-zinc-400
                    ">
                        {result.missconceptions.map(
                        (point) => (
                            <li key={point}>
                            • {point}
                            </li>
                        )
                        )}
                    </ul>

                </div>

            )}

            <div className="
                mt-8
                rounded-2xl
                bg-zinc-950
                p-5
                "
            >
                <p className="
                    text-xs
                    uppercase
                    tracking-wide
                    text-zinc-500
                ">
                Expected answer
                </p>

                <p className="
                    mt-3
                    leading-relaxed
                    text-zinc-300
                ">
                {result.expected_answer}
                </p>
            </div>

            <div
        className="
          mt-8
          grid
          gap-4
          sm:grid-cols-2
        "
      >

        <div
          className="
            rounded-2xl
            border border-zinc-800
            p-5
          "
        >
          <p
            className="
              text-sm
              text-zinc-500
            "
          >
            Mastery
          </p>

          <p
            className="
              mt-2
              text-xl
              font-semibold
            "
          >
            {masteryBefore}%
            {" → "}
            {masteryAfter}%
          </p>
        </div>


        <div
          className="
            rounded-2xl
            border border-zinc-800
            p-5
          "
        >
          <p
            className="
              text-sm
              text-zinc-500
            "
          >
            Memory stability
          </p>

          <p
            className="
              mt-2
              text-xl
              font-semibold
            "
          >
            {result.stability_before.toFixed(1)}
            {" → "}
            {result.stability_after.toFixed(1)}
            {" days"}
          </p>
        </div>

      </div>


      <div
        className="
          mt-6
          flex
          items-center
          justify-between
        "
      >
        <div>

          <p
            className="
              text-sm
              text-zinc-500
            "
          >
            Scheduler
          </p>

          <p
            className="
              font-medium
            "
          >
            {result.scheduler_rating}
          </p>

        </div>


        <button
          onClick={onNext}

          className="
            rounded-xl
            bg-zinc-100
            px-6
            py-3
            font-medium
            text-zinc-950
          "
        >
          Next question
        </button>

      </div>

    </div>
  );
}