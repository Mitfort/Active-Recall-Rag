"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Background,
  Controls,
  MarkerType,
  MiniMap,
  ReactFlow,
  type Edge,
  type NodeTypes,
  type ReactFlowInstance,
} from "@xyflow/react";
import { GRAPH_NODE_WIDTH, layoutGraph } from "@/app/lib/graphLayout";
import { KnowledgeNode, type KnowledgeFlowNode } from "./KnowledgeNode";
import { NoteDetailsPanel } from "./NoteDetailsPanel";
import type { KnowledgeGraphData } from "@/app/types/api";

type Props = { graph: KnowledgeGraphData };

const nodeTypes: NodeTypes = { knowledge: KnowledgeNode };

export function KnowledgeGraph({ graph }: Props) {
  const [selectedNoteId, setSelectedNoteId] = useState<number | null>(null);
  const [showSemantic, setShowSemantic] = useState(true);
  const [expandedNoteIds, setExpandedNoteIds] = useState<Set<number>>(() => new Set());
  const [flow, setFlow] = useState<ReactFlowInstance<KnowledgeFlowNode> | null>(null);

  const toggleConcepts = useCallback((noteId: number) => {
    setExpandedNoteIds((current) => {
      const next = new Set(current);
      if (next.has(noteId)) next.delete(noteId);
      else next.add(noteId);
      return next;
    });
  }, []);

  const { nodes, edges } = useMemo(() => {
    const visibleNodes = graph.nodes.filter((node) => node.type !== "concept"
      || (node.note_id !== null && expandedNoteIds.has(node.note_id)));
    const visibleNodeIds = new Set(visibleNodes.map((node) => String(node.id)));
    const graphNodes = new Map(graph.nodes.map((node) => [String(node.id), node]));
    const owningNoteIds = new Map(visibleNodes.filter((node) => node.type === "note")
      .map((node) => [node.note_id, String(node.id)]));
    const visibleEndpoint = (id: number | string) => {
      if (visibleNodeIds.has(String(id))) return String(id);
      const node = graphNodes.get(String(id));
      return node?.type === "concept" ? owningNoteIds.get(node.note_id) : undefined;
    };
    const flowNodes: KnowledgeFlowNode[] = visibleNodes.map((node) => ({
      id: String(node.id),
      type: "knowledge",
      position: { x: 0, y: 0 },
      style: {
        width: GRAPH_NODE_WIDTH,
        height: node.type === "domain" || node.type === "topic"
          ? 128
          : node.type === "note" && node.concept_count > 0 ? 256 : 216,
      },
      data: {
        label: node.label,
        subject: node.subject,
        kind: node.type,
        noteId: node.note_id,
        depth: node.depth,
        mastery: node.mastery,
        retrievability: node.retrievability,
        conceptCount: node.concept_count,
        reviewedCount: node.reviewed_count,
        expanded: node.note_id !== null && expandedNoteIds.has(node.note_id),
        onToggleConcepts: node.type === "note" ? toggleConcepts : undefined,
      },
    }));

    const seenRelations = new Set<string>();
    const flowEdges: Edge[] = graph.edges.flatMap((edge, index) => {
      const semantic = edge.type === "semantic";
      const hierarchy = edge.type === "hierarchy";
      // A heading link remains a note-to-note relation while its concept is collapsed.
      const source = hierarchy ? String(edge.source) : visibleEndpoint(edge.source);
      const target = hierarchy ? String(edge.target) : visibleEndpoint(edge.target);
      if (!source || !target || source === target
        || !visibleNodeIds.has(source) || !visibleNodeIds.has(target)) return [];
      const relationKey = JSON.stringify([edge.type, source, target]);
      if (seenRelations.has(relationKey)) return [];
      seenRelations.add(relationKey);
      const color = hierarchy ? "#52525b" : semantic ? "#a78bfa" : "#38bdf8";

      return [{
        id: `edge-${edge.source}-${edge.target}-${index}`,
        source,
        target,
        type: "smoothstep",
        data: { relation: edge.type },
        markerEnd: semantic ? undefined : { type: MarkerType.ArrowClosed, color },
        style: {
          stroke: color,
          strokeWidth: hierarchy ? 1.5 : 2,
          ...(semantic ? { strokeDasharray: "7 7", opacity: 0.55 } : {}),
        },
        label: semantic && edge.score !== null
          ? `${Math.round(edge.score * 100)}%`
          : undefined,
        labelStyle: { fontSize: 10, fill: "#a78bfa" },
        ariaLabel: `${edge.type}: ${source} to ${target}${edge.heading ? `, ${edge.heading}` : ""}`,
      }];
    });

    // A missing title can be referenced at multiple depths. Keep a placeholder
    // beside each source so its rank always follows the referring note.
    const sourceDepths = new Map(flowNodes.map((node) => [node.id, node.data.depth]));
    const missingNodes = new Set<string>();
    for (const unresolved of graph.unresolved_links) {
      const source = String(unresolved.source);
      const depth = sourceDepths.get(source);
      if (depth === undefined) continue;
      const missingId = `missing:${source}:${encodeURIComponent(unresolved.target_title)}`;
      if (!missingNodes.has(missingId)) {
        missingNodes.add(missingId);
        flowNodes.push({
          id: missingId,
          type: "knowledge",
          position: { x: 0, y: 0 },
          style: { width: GRAPH_NODE_WIDTH, height: 152 },
          data: {
            label: unresolved.target_title,
            subject: "Knowledge gap",
            kind: "missing",
            noteId: null,
            depth: depth + 1,
            mastery: 0,
            retrievability: 0,
            conceptCount: 0,
            reviewedCount: 0,
            expanded: false,
          },
        });
        flowEdges.push({
          id: `missing-edge-${missingId}`,
          source,
          target: missingId,
          type: "smoothstep",
          data: { relation: "wikilink" },
          style: { stroke: "#38bdf8", strokeDasharray: "3 4" },
          markerEnd: { type: MarkerType.ArrowClosed, color: "#38bdf8" },
        });
      }
    }

    return layoutGraph(flowNodes, flowEdges);
  }, [graph, expandedNoteIds, toggleConcepts]);

  useEffect(() => {
    if (!flow) return;
    const frame = requestAnimationFrame(() => {
      void flow.fitView({ padding: 0.15, duration: 200 });
    });
    return () => cancelAnimationFrame(frame);
  }, [flow, nodes]);

  const visibleEdges = useMemo(
    () => showSemantic ? edges : edges.filter((edge) => edge.data?.relation !== "semantic"),
    [edges, showSemantic],
  );

  return (
    <div className="relative flex h-[72vh] min-h-[600px] flex-col overflow-hidden rounded-3xl border border-zinc-800 bg-zinc-950">
      <div className="flex shrink-0 flex-wrap items-center gap-x-5 gap-y-3 border-b border-zinc-800 bg-zinc-950 px-4 py-3 text-xs">
        <div className="mr-auto">
          <p className="font-medium text-zinc-300">General → detailed</p>
          <p className="mt-1 text-zinc-500">Folder domains → tag topics → notes → concepts</p>
        </div>
        <div className="flex items-center gap-3 text-zinc-500">
          <div className="h-px w-8 bg-zinc-600" />
          Hierarchy
        </div>
        <div className="flex items-center gap-3 text-zinc-500">
          <div className="h-0.5 w-8 bg-sky-400" />
          Wikilink
        </div>
        <div className="flex items-center gap-3 text-zinc-500">
          <div className="w-8 border-t border-dashed border-violet-400" />
          Semantic suggestion
        </div>
        <button
          onClick={() => setShowSemantic((value) => !value)}
          aria-pressed={showSemantic}
          className="rounded-lg border border-zinc-800 px-3 py-2 text-zinc-400 transition hover:border-zinc-600 hover:text-zinc-200"
        >
          {showSemantic ? "Hide suggestions" : "Show suggestions"}
        </button>
      </div>

      <div className="min-h-0 flex-1">
        <ReactFlow<KnowledgeFlowNode>
          nodes={nodes}
          edges={visibleEdges}
          nodeTypes={nodeTypes}
          onInit={setFlow}
          fitView
          minZoom={0.05}
          maxZoom={2}
          onNodeClick={(_event, node) => {
            if (node.data.noteId !== null) setSelectedNoteId(node.data.noteId);
          }}
        >
          <Background gap={24} size={1} />
          <Controls />
          <MiniMap
            pannable
            zoomable
            style={{ width: 140, height: 100 }}
            bgColor="#09090b"
            maskColor="rgba(9, 9, 11, 0.7)"
            nodeColor="#3f3f46"
            nodeStrokeColor="#71717a"
          />
        </ReactFlow>
      </div>

      <NoteDetailsPanel noteId={selectedNoteId} onClose={() => setSelectedNoteId(null)} />
    </div>
  );
}
