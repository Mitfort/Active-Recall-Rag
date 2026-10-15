import {
  Suspense,
} from "react";

import {
  DashboardContent,
} from "@/app/components/dashboard/DashboardContent";


function DashboardLoading() {
  return (
    <div className="mt-6 space-y-6">

      <div
        className="
          h-44
          animate-pulse
          rounded-3xl
          bg-zinc-900
        "
      />

      <div
        className="
          grid
          gap-4
          sm:grid-cols-2
          xl:grid-cols-4
        "
      >
        {Array.from({
          length: 4,
        }).map((_, index) => (

          <div
            key={index}
            className="
              h-32
              animate-pulse
              rounded-2xl
              bg-zinc-900
            "
          />

        ))}
      </div>

    </div>
  );
}


export default function Home() {

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


        <Suspense
          fallback={
            <DashboardLoading />
          }
        >
          <DashboardContent />
        </Suspense>

      </div>
    </main>
  );
}