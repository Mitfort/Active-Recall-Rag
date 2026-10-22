import dagre from "@dagrejs/dagre";
import { Position, type Edge, type Node } from "@xyflow/react";

export const GRAPH_NODE_WIDTH = 240;

const DEFAULT_NODE_HEIGHT = 216;
const NODE_GAP = 40;
const COLUMN_GAP = 120;
const MARGIN = 40;

export function layoutGraph<NodeType extends Node>(
    nodes: NodeType[],
    edges: Edge[],
) {
    const graph = new dagre.graphlib.Graph();
    graph.setDefaultEdgeLabel(() => ({}));
    graph.setGraph({
        rankdir: "LR",
        nodesep: NODE_GAP,
        ranksep: COLUMN_GAP,
        marginx: MARGIN,
        marginy: MARGIN,
    });

    const nodeHeights = new Map<string, number>();
    for (const node of nodes) {
        const height = typeof node.style?.height === "number"
            ? node.style.height
            : DEFAULT_NODE_HEIGHT;
        nodeHeights.set(node.id, height);
        graph.setNode(node.id, { width: GRAPH_NODE_WIDTH, height });
    }

    // Cross-links describe related subjects; only the hierarchy orders them.
    for (const edge of edges) {
        if (edge.data?.relation === "hierarchy") {
            graph.setEdge(edge.source, edge.target);
        }
    }
    dagre.layout(graph);

    const columns = new Map<number, NodeType[]>();
    for (const node of nodes) {
        const depth = typeof node.data.depth === "number" ? node.data.depth : 0;
        const column = columns.get(depth) ?? [];
        column.push(node);
        columns.set(depth, column);
    }

    const positions = new Map<string, { x: number; y: number }>();
    for (const [depth, column] of columns) {
        column.sort((left, right) => graph.node(left.id).y - graph.node(right.id).y);
        let nextY = MARGIN;
        for (const node of column) {
            const height = nodeHeights.get(node.id)!;
            const y = Math.max(nextY, graph.node(node.id).y - height / 2);
            positions.set(node.id, {
                x: MARGIN + depth * (GRAPH_NODE_WIDTH + COLUMN_GAP),
                y,
            });
            nextY = y + height + NODE_GAP;
        }
    }

    return {
        nodes: nodes.map((node) => ({
            ...node,
            sourcePosition: Position.Right,
            targetPosition: Position.Left,
            position: positions.get(node.id)!,
        })),
        edges,
    };
}
