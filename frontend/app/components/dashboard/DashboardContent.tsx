import {
  getDashboard,
} from "../../lib/api";

import {
  StatCard,
} from "@/app/components/dashboard/StatCard";

import {
  WeakConcepts,
} from "@/app/components/dashboard/WeakConcepts";

import {
  ReviewActivity,
} from "@/app/components/dashboard/ReviewActivity";

import {
  TodayReview,
} from "@/app/components/dashboard/TodaysReview";

export async function DashboardContent() {

  const dashboard =
    await getDashboard();


  const mastery =
    Math.round(
      dashboard.average_mastery
      * 100
    );


  const memory =
    Math.round(
      dashboard.average_retrievability
      * 100
    );


  const accuracy =
    dashboard.recent_accuracy === null

      ? "—"

      : `${Math.round(
          dashboard.recent_accuracy
          * 100
        )}%`;


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
          max-w-7xl
          px-6
          py-10
          lg:px-8
        "
      >

        <header className="mb-10">

          <p
            className="
              text-sm
              font-medium
              text-zinc-500
            "
          >
            Adaptive Learning System
          </p>

          <h1
            className="
              mt-2
              text-2xl
              font-semibold
              tracking-tight
            "
          >
            Learning Dashboard
          </h1>

        </header>


        <TodayReview
          dueToday={
            dashboard.due_today
          }
        />


        <section
          className="
            mt-6
            grid
            gap-4
            sm:grid-cols-2
            xl:grid-cols-4
          "
        >
          <StatCard
            label="Concepts"
            value={
              dashboard.total_concepts
            }
            description={
              `${dashboard.new_concepts}
               not reviewed yet`
            }
          />

          <StatCard
            label="Average mastery"
            value={`${mastery}%`}
            description={
              "Long-term concept understanding"
            }
          />

          <StatCard
            label="Current memory"
            value={`${memory}%`}
            description={
              "Estimated retrievability"
            }
          />

          <StatCard
            label="Recent accuracy"
            value={accuracy}
            description={
              `${dashboard.reviews_last_7_days}
               reviews in 7 days`
            }
          />
        </section>


        <section
          className="
            mt-6
            grid
            gap-6
            lg:grid-cols-[1.4fr_1fr]
          "
        >

          <ReviewActivity
            activity={
              dashboard.activity
            }
          />

          <WeakConcepts
            concepts={
              dashboard.weakest
            }
          />

        </section>

      </div>
    </main>
  );
}