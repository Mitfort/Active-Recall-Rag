"use client";

import { Handle, Position, type Node, type NodeProps } from "@xyflow/react";
import type { KnowledgeGraphNode } from "@/app/types/api";

export type KnowledgeNodeData = {
    label: string;
    subject: string;
    kind: KnowledgeGraphNode["type"] | "missing";
    noteId: number | null;
    depth: number;
    mastery: number;
    retrievability: number;
    conceptCount: number;
    reviewedCount: number;
    expanded: boolean;
    onToggleConcepts?: (noteId: number) => void;
};

export type KnowledgeFlowNode = Node<KnowledgeNodeData, "knowledge">;

const kindLabels = {
    domain: "Folder domain",
    topic: "Tag topic",
    note: "Note",
    concept: "Concept",
    missing: "Missing note",
};

export function KnowledgeNode({ data }: NodeProps<KnowledgeFlowNode>) {
    const grouping = data.kind === "domain" || data.kind === "topic";
    const missing = data.kind === "missing";
    let statusClasses = "border-zinc-700 bg-zinc-900";

    if (missing) {
        statusClasses = "border-dashed border-zinc-700 bg-zinc-950";
    } else if (data.kind === "domain") {
        statusClasses = "border-sky-900 bg-sky-950/40";
    } else if (data.kind === "topic") {
        statusClasses = "border-violet-900 bg-violet-950/30";
    } else if (data.reviewedCount > 0) {
        statusClasses = data.mastery >= 0.75
            ? "border-emerald-900 bg-emerald-950/30"
            : data.mastery >= 0.4
                ? "border-amber-900 bg-amber-950/20"
                : "border-rose-900 bg-rose-950/20";
    }

    return (
        <div className={`h-full w-full rounded-2xl border p-4 shadow-xl ${statusClasses}`}>
            <Handle type="target" position={Position.Left} />

            <div className="flex items-center gap-2 text-xs text-zinc-500">
                <span className="shrink-0">{kindLabels[data.kind]}</span>
                {!grouping && !missing && (
                    <span className="truncate" title={data.subject}>{data.subject}</span>
                )}
            </div>

            <p
                className="mt-1 line-clamp-2 min-h-10 text-sm font-semibold leading-5 text-zinc-100 [overflow-wrap:anywhere]"
                title={data.label}
            >
                {data.label}
            </p>

            {missing ? (
                <p className="mt-2 text-xs leading-4 text-zinc-500">
                    Referenced in your notes; no matching note exists yet.
                </p>
            ) : grouping ? (
                <p className="mt-2 truncate text-xs text-zinc-500" title={data.subject || "data/notes"}>
                    {data.subject || "data/notes"}
                </p>
            ) : (
                <>
                    <p className="mt-2 text-xs text-zinc-500">
                        {data.kind === "concept"
                            ? data.reviewedCount > 0 ? "Reviewed concept" : "Not reviewed yet"
                            : `${data.conceptCount} concepts • ${data.reviewedCount} reviewed`}
                    </p>

                    <div className="mt-3 grid grid-cols-2 gap-3">
                        <div>
                            <p className="text-[10px] uppercase tracking-wide text-zinc-600">Mastery</p>
                            <p className="mt-1 text-sm font-medium">{Math.round(data.mastery * 100)}%</p>
                        </div>
                        <div>
                            <p className="text-[10px] uppercase tracking-wide text-zinc-600">Memory</p>
                            <p className="mt-1 text-sm font-medium">{Math.round(data.retrievability * 100)}%</p>
                        </div>
                    </div>

                    {data.kind === "note" && data.conceptCount > 0 && (
                        <button
                            type="button"
                            className="nodrag nopan mt-3 rounded-md border border-zinc-700 px-2 py-1.5 text-xs text-zinc-300 hover:border-zinc-500 hover:text-zinc-100"
                            aria-expanded={data.expanded}
                            onClick={(event) => {
                                event.stopPropagation();
                                if (data.noteId !== null) data.onToggleConcepts?.(data.noteId);
                            }}
                        >
                            {data.expanded ? "Hide concepts" : `Show ${data.conceptCount} concepts`}
                        </button>
                    )}
                </>
            )}

            {!missing && <Handle type="source" position={Position.Right} />}
        </div>
    );
}
