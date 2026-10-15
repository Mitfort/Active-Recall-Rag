import Link from "next/link";

type Props = {
  dueToday: number;
};


export function TodayReview({
  dueToday,
}: Props) {

  return (
    <section
      className="
        relative
        overflow-hidden
        rounded-3xl
        border border-zinc-800
        bg-zinc-900
        p-8
      "
    >
      <div
        className="
          absolute
          -right-16
          -top-16
          h-48
          w-48
          rounded-full
          bg-zinc-700/20
          blur-3xl
        "
      />


      <div
        className="
          relative
          flex
          flex-col
          gap-6
          md:flex-row
          md:items-center
          md:justify-between
        "
      >
        <div>
          <p
            className="
              text-sm
              font-medium
              text-zinc-400
            "
          >
            Daily active recall
          </p>

          <h1
            className="
              mt-2
              text-3xl
              font-semibold
              tracking-tight
              text-zinc-50
            "
          >
            {dueToday > 0
              ? `${dueToday} concepts are ready`
              : "You're caught up"}
          </h1>

          <p
            className="
              mt-3
              max-w-xl
              text-zinc-400
            "
          >
            Your review queue is selected
            using mastery, memory stability
            and estimated retrievability.
          </p>
        </div>


        {dueToday > 0 && (

          <Link
            href="/review"
            className="
              inline-flex
              items-center
              justify-center
              rounded-xl
              bg-zinc-100
              px-6
              py-3
              font-medium
              text-zinc-950
              transition
              hover:bg-white
            "
          >
            Start review
          </Link>

        )}
      </div>
    </section>
  );
}