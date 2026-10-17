"use client";

import {
    Handle,
    Position,
    type Node,
    type NodeProps
} from "@xyflow/react";

export type KnowledgeNodeData = {
    label: string;
    subject: string;
    kind: "note" | "missing";
    mastery: number;
    retrievability: number;

    conceptCount: number;
    reviewedCount: number;
};

export type KnowledgeFlowNode = Node<KnowledgeNodeData,"knowledge">;

export function KnowledgeNode({
    data,
}: NodeProps<KnowledgeFlowNode>) { 

    if (data.kind === "missing") {
        return (
            <div className="
                w-[240px]
                rounded-2xl
                border
                border-dashed
                border-zinc-700
                bg-zinc-950
                p-4
            ">
                <Handle
                    type="target"
                    position={Position.Left}
                />

                <p className="
                    text-xs
                    font-medium
                    uppercase
                    text-zinc-600
                ">
                    Missing Note
                </p>

                <p className="
                    mt-2
                    font-medium
                    text-zinc-400
                ">
                    {data.label}
                </p>

                <p className="
                    mt-2
                    text-xs
                    text-zinc-600
                ">
                    Referenced in your notes, but no note exists with this title yet.
                </p>

            </div>
        )

    } 

    const mastery = Math.round(data.mastery * 100);
    const memory = Math.round(data.retrievability * 100);

    let statusClasses = `
        border-zinc-700
        bg-zinc-900
    `;

    if (data.reviewedCount > 0) {
        if (data.mastery >= 0.75) {
            statusClasses = `
                border-emerald-900
                bg-emerald-950/30
            `;
        }
        else if (data.mastery >= 0.4) {
            statusClasses = `
                border-amber-900
                bg-amber-950/20
            `;
        }
        else {
            statusClasses = `
                border-rose-900
                bg-rose-950/20
            `;
        }
    }

    return (
        <div className={`
            w-[240px]
            rounded-2xl
            border
            p-4
            shadow-xl
            transition
            ${statusClasses}
        `}>
            <Handle
                type="target"
                position={Position.Left}
            />

            <p className="
                text-xs
                text-zinc-500
            ">
                {data.subject}
            </p>

            <p className="
                mt-1
                font-semibold
                text-zinc-100
            ">
                {data.label}
            </p>

            <p className="
                mt-2
                text-xs
                text-zinc-500
            ">
                {data.conceptCount}
                {" concepts • "}
                {data.reviewedCount}
                {" reviewed"}
            </p>

            <div className="
                mt-4
                grid
                grid-cols-2
                gap-3
            ">
                <div>
                    <p className="
                        text-[10px]
                        uppercase
                        tracking-wide
                        text-zinc-600
                    ">
                        Mastery
                    </p>

                    <p className="
                        mt-1
                        text-sm
                        font-medium
                    ">
                        {mastery}%
                    </p>
                </div>

                <div>
                    <p className="
                        text-[10px]
                        uppercase
                        tracking-wide
                        text-zinc-600
                    ">
                        Memory
                    </p>

                    <p className="
                        mt-1
                        text-sm
                        font-medium
                    ">
                        {memory}%
                    </p>
                </div>

            </div>

            <Handle
                type="source"
                position={Position.Right}
            />
        </div>
    )
}