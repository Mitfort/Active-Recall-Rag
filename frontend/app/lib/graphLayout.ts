import dagre from "@dagrejs/dagre";

import {
    Position,
    type Edge,
    type Node,
} from "@xyflow/react";

const NODE_WIDTH = 240;
const NODE_HEIGHT = 130;

export function layoutGraph(
    nodes: Node[],
    edges: Edge[]
) {
    const graph = new dagre.graphlib.Graph();

    graph.setDefaultEdgeLabel(() => ({}));

    graph.setGraph({
        rankdir: "LR",
        nodesep: 60,
        ranksep:120,
        marginx: 40,
        marginy: 40,
    });

    for (const node of nodes) {
        graph.setNode(
            node.id,
            {
                width: NODE_WIDTH,
                height: NODE_HEIGHT,
            }
        )
    }

    for (const edge of edges) {
        graph.setEdge(edge.source, edge.target);
    }

    dagre.layout(graph);

    const layoutedNodes = nodes.map((node) => {
        const position = graph.node(node.id);

        return {
            ...node,

            sourcePosition: Position.Right,
            targetPosition: Position.Left,

            position: {
                x: position.x - NODE_WIDTH / 2,
                y: position.y - NODE_HEIGHT / 2,
            }
        }
    });

    return {
        nodes: layoutedNodes,
        edges: edges
    }
}