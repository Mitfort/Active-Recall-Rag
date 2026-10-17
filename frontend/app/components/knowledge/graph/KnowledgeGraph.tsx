"use client";


import {
  useMemo,
  useState,
} from "react";

import {
  Background,
  Controls,
  MarkerType,
  MiniMap,
  ReactFlow,
  type Edge,
  type NodeTypes,
} from "@xyflow/react";


import {
  layoutGraph,
} from "@/app/lib/graphLayout";


import {
  KnowledgeNode,
  type KnowledgeFlowNode,
} from "./KnowledgeNode";


import {
  NoteDetailsPanel,
} from "./NoteDetailsPanel";


import type {
  KnowledgeGraphData,
} from "@/app/types/api";


type Props = {
  graph: KnowledgeGraphData;
};


const nodeTypes: NodeTypes = {
  knowledge: KnowledgeNode,
};


export function KnowledgeGraph({
  graph,
}: Props) {

  const [selectedNoteId,setSelectedNoteId] = useState<number | null>(null);
  const [showSemantic, setShowSemantic] = useState(true);

  const {
    nodes,
    edges,
  } = useMemo(() => {

    const flowNodes:
      KnowledgeFlowNode[] =
      graph.nodes.map(
        (node) => ({
          id: String(
            node.id
          ),

          type: "knowledge",

          position: {
            x: 0,
            y: 0,
          },

          data: {
            label:
              node.label,

            subject:
              node.subject,

            kind:
              "note",

            mastery:
              node.mastery,

            retrievability:
              node.retrievability,

            conceptCount:
              node.concept_count,

            reviewedCount:
              node.reviewed_count,
          },
        })
      );

    const visibleGraphEdges = graph.edges.filter((edge) => showSemantic || edge.type !== "semantic");

    const flowEdges:
    Edge[] =
    visibleGraphEdges.map(
      (edge, index) => {

        const semantic = edge.type === "semantic";
          
        return {
          id:
            `edge-${edge.source}-${edge.target}-${index}`,

          source:
            String(
              edge.source
            ),
          target:
            String(
              edge.target
            ),

          type:
            "smoothstep",

          markerEnd:semantic ? undefined : {
                    type:
                      MarkerType.ArrowClosed,
          },

          style:
            semantic ? {
              strokeDasharray:"7 7",
              opacity: 0.55,
            }

                : {
                    strokeWidth: 2,
                  },

            label:
              semantic
              && edge.score !== null

                ? `${Math.round(
                    edge.score * 100
                  )}%`

                : undefined,

            labelStyle:
              semantic

                ? {
                    fontSize: 10,
                    fill: "#71717a",
                  }

                : undefined,
          };
        }
    );

    //
    // Missing / unresolved notes
    //

    const missingNodeIds =
      new Map<
        string,
        string
      >();


    for (
      const unresolved
      of graph.unresolved_links
    ) {

      let missingId =
        missingNodeIds.get(
          unresolved.target_title
        );


      if (!missingId) {

        missingId =
          `missing:${encodeURIComponent(
            unresolved.target_title
          )}`;


        missingNodeIds.set(
          unresolved.target_title,
          missingId
        );


        flowNodes.push({
          id: missingId,

          type: "knowledge",

          position: {
            x: 0,
            y: 0,
          },

          data: {
            label:
              unresolved.target_title,

            subject:
              "Knowledge gap",

            kind:
              "missing",

            mastery: 0,

            retrievability: 0,

            conceptCount: 0,

            reviewedCount: 0,
          },
        });
      }


      flowEdges.push({
        id:
          `missing-edge-${unresolved.source}-${missingId}`,

        source:
          String(
            unresolved.source
          ),

        target:
          missingId,

        type:
          "smoothstep",

        animated: true,
      });
    }


    return layoutGraph(
      flowNodes,
      flowEdges,
    );

  }, [graph,showSemantic]);


  return (
    <div
      className="
        relative
        h-[72vh]
        min-h-[600px]
        overflow-hidden
        rounded-3xl
        border
        border-zinc-800
        bg-zinc-950
      "
    >

      <div
  className="
    absolute
    left-4
    top-4
    z-20
    rounded-xl
    border border-zinc-800
    bg-zinc-950/90
    p-4
    text-xs
    backdrop-blur
  "
>

  <p
    className="
      mb-3
      font-medium
      text-zinc-300
    "
  >
    Relations
  </p>


  <div
    className="
      flex
      items-center
      gap-3
      text-zinc-500
    "
  >

        <div
          className="
            h-px
            w-8
            bg-zinc-400
          "
        />

        Wikilink

      </div>


        <div
          className="
            mt-2
            flex
            items-center
            gap-3
            text-zinc-500
          "
        >

          <div
            className="
              w-8
              border-t
              border-dashed
              border-zinc-500
            "
          />

          Semantic suggestion

        </div>

        <button onClick={() => {
          setShowSemantic((value) => !value)
        }}
          className="
            mt-4
            w-full
            rounded-lg
            border border-zinc-800
            px-3
            py-2
            text-zinc-400
            transition
            hover:border-zinc-600
            hover:text-zinc-200
          "
        >
          {showSemantic ? "Hide suggestions" : "Show suggestions"}

        </button>

      </div>

      <ReactFlow
        nodes={nodes}

        edges={edges}

        nodeTypes={
          nodeTypes
        }

        fitView

        minZoom={0.15}

        maxZoom={2}

        onNodeClick={(
          _event,
          node,
        ) => {

          if (
            node.id.startsWith(
              "missing:"
            )
          ) {
            return;
          }

          setSelectedNoteId(
            Number(node.id)
          );
        }}
      >

        <Background
          gap={24}
          size={1}
        />

        <Controls />

        <MiniMap
          pannable
          zoomable
        />

      </ReactFlow>


      <NoteDetailsPanel
        noteId={
          selectedNoteId
        }

        onClose={() =>
          setSelectedNoteId(
            null
          )
        }
      />

    </div>
  );
}