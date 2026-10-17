import {
  Suspense,
} from "react";


import {
  getKnowledgeGraph,
} from "@/app/lib/api";


import {
  KnowledgeGraph,
} from "@/app/components/knowledge/graph/KnowledgeGraph";


async function GraphContent() {

  const graph =
    await getKnowledgeGraph();


  return (
    <KnowledgeGraph
      graph={graph}
    />
  );
}


function GraphLoading() {

  return (
    <div
      className="
        h-[72vh]
        min-h-[600px]
        animate-pulse
        rounded-3xl
        bg-zinc-900
      "
    />
  );
}


export default function KnowledgeGraphPage() {

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
          max-w-[1600px]
          px-6
          py-10
        "
      >

        <header
          className="
            mb-8
          "
        >

          <p
            className="
              text-sm
              text-zinc-500
            "
          >
            Knowledge map
          </p>


          <h1
            className="
              mt-2
              text-3xl
              font-semibold
              tracking-tight
            "
          >
            Knowledge Graph
          </h1>


          <p
            className="
              mt-3
              max-w-2xl
              text-zinc-400
            "
          >
            Relationships discovered
            from your Obsidian wikilinks.
            Missing nodes represent
            referenced topics that do
            not yet have their own note.
          </p>

        </header>


        <Suspense
          fallback={
            <GraphLoading />
          }
        >
          <GraphContent />
        </Suspense>

      </div>

    </main>
  );
}