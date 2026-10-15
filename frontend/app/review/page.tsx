import {
  Suspense,
} from "react";

import {
  getTodayReview,
} from "@/app/lib/api";

import {
    ReviewSession
} from "@/app/components/review/ReviewSession";


async function ReviewLoader() {

  const review =
    await getTodayReview();

  return (
    <ReviewSession
      concepts={review.concepts}
    />
  );
}


function ReviewLoading() {

  return (
    <div
      className="
        h-80
        animate-pulse
        rounded-3xl
        bg-zinc-900
      "
    />
  );
}


export default function ReviewPage() {

  return (
    <main
      className="
        min-h-screen
        bg-zinc-950
        text-zinc-100
      "
    >
      <div
        className="
          mx-auto
          max-w-3xl
          px-6
          py-12
        "
      >

        <Suspense
          fallback={
            <ReviewLoading />
          }
        >
          <ReviewLoader />
        </Suspense>

      </div>
    </main>
  );
}