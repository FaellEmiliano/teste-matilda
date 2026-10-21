import { useEffect, useMemo, useState } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MarkerType,
  type Node,
  type Edge,
  useNodesState,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import type { Analysis, GraphNode, Match } from "../types";
import { Network, Layers } from "lucide-react";
export const typeNames: Record<GraphNode["type"], string> = {
  PAPER: "Artigo",
  RESEARCHER: "Pessoa · autoria",
  CONCEPT: "Conceito",
  CONTRIBUTION: "Contribuição",
  EVIDENCE: "Documento",
};
export const relationNames: Record<string, string> = {
  CITES: "Cita",
  AUTHORED_BY: "Tem autoria de",
  ADDRESSES: "Aborda",
  MADE_CONTRIBUTION: "Participou de",
  RELATED_TO: "Relação temática",
  SUPPORTED_BY: "Sustentada por",
  DOCUMENTED_INFLUENCE: "Influência documentada",
};
const colors = {
  PAPER: "#254f44",
  RESEARCHER: "#81583c",
  CONCEPT: "#506781",
  CONTRIBUTION: "#785c80",
  EVIDENCE: "#666a5e",
};
export function ScientificGraph({
  analysis,
  selected,
  onSelect,
}: {
  analysis: Analysis;
  selected: Match | null;
  onSelect: (node: GraphNode) => void;
}) {
  const [layer, setLayer] = useState("all");
  const { nodes, edges } = useMemo(() => {
    const visibleEdges = analysis.graph.edges.filter(
      (e) =>
        layer === "all" ||
        (layer === "citation"
          ? ["CITES", "AUTHORED_BY"].includes(e.relation_type)
          : !["CITES", "AUTHORED_BY"].includes(e.relation_type)),
    );
    const visibleIds = new Set([
      analysis.paper.id,
      ...visibleEdges.flatMap((e) => [e.source, e.target]),
    ]);
    const activeIds = new Set(
      selected
        ? [
            analysis.paper.id,
            "contribution:" + selected.contribution.id,
            ...selected.matched_concepts.map((c) => "concept:" + c.id),
            ...selected.researchers.map(
              (r) => r.openalex_id || "researcher:" + r.id,
            ),
            ...selected.evidence.map((e) => e.id),
          ]
        : [],
    );
    const groups: Record<string, GraphNode[]> = {};
    for (const n of analysis.graph.nodes.filter((n) => visibleIds.has(n.id))) {
      const key = n.id === analysis.paper.id ? "ROOT" : n.type;
      (groups[key] ??= []).push(n);
    }
    const columns: Record<string, number> = {
      ROOT: 0,
      PAPER: -350,
      CONCEPT: 340,
      CONTRIBUTION: 700,
      RESEARCHER: 1050,
      EVIDENCE: 1400,
    };
    const flowNodes: Node[] = Object.entries(groups).flatMap(([type, group]) =>
      group.map((n, i) => ({
        id: n.id,
        position: { x: columns[type], y: (i - (group.length - 1) / 2) * 145 },
        data: {
          label: (
            <div className="graph-node-content">
              <span>
                {n.id === analysis.paper.id
                  ? "ARTIGO ANALISADO"
                  : typeNames[n.type]}
              </span>
              <strong>
                {n.label.length > 95 ? n.label.slice(0, 92) + "…" : n.label}
              </strong>
            </div>
          ),
        },
        style: {
          width: 245,
          border: `${activeIds.has(n.id) ? "2" : "1"}px solid ${colors[n.type]}`,
          background: n.id === analysis.paper.id ? "#254f44" : "#fffefa",
          color: n.id === analysis.paper.id ? "#fffefa" : "#233e34",
          borderRadius: n.type === "RESEARCHER" ? 34 : 12,
          opacity: selected && !activeIds.has(n.id) ? 0.35 : 1,
        },
        ariaLabel: typeNames[n.type] + ": " + n.label,
      })),
    );
    const flowEdges: Edge[] = visibleEdges.map((e) => {
      const active = activeIds.has(e.source) && activeIds.has(e.target);
      return {
        id: e.id,
        source: e.source,
        target: e.target,
        label: relationNames[e.relation_type],
        type: "default",
        animated: false,
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: e.verification_status === "thematic" ? "#8496ac" : "#527968",
        },
        style: {
          stroke: active
            ? "#a35d33"
            : e.verification_status === "thematic"
              ? "#8496ac"
              : "#527968",
          strokeWidth: active ? 2.5 : 1.3,
          strokeDasharray:
            e.verification_status === "thematic" ? "6 5" : undefined,
          opacity: selected && !active ? 0.16 : 0.85,
        },
        labelStyle: { fontSize: 10, fill: "#364d42" },
        ariaLabel: relationNames[e.relation_type],
        data: { explanation: e.explanation },
      };
    });
    return { nodes: flowNodes, edges: flowEdges };
  }, [analysis, selected, layer]);
  const [flowNodes, setFlowNodes, onNodesChange] = useNodesState<Node>(nodes);
  useEffect(() => {
    setFlowNodes((previous) =>
      nodes.map((n) => {
        const old = previous.find((p) => p.id === n.id);
        return {
          ...n,
          position: old?.position ?? n.position,
          measured: old?.measured,
        };
      }),
    );
  }, [nodes, setFlowNodes]);
  return (
    <section className="graph-panel" aria-label="Grafo científico interativo">
      <div className="panel-toolbar">
        <div>
          <Network size={16} />
          <strong>Mapa da investigação</strong>
        </div>
        <span>
          {nodes.length} nós · {edges.length} conexões
        </span>
      </div>
      <div className="graph-layers">
        <Layers size={14} />
        {[
          ["all", "Duas redes"],
          ["citation", "Bibliografia"],
          ["contribution", "Contribuições"],
        ].map(([value, label]) => (
          <button
            key={value}
            aria-pressed={layer === value}
            onClick={() => setLayer(value)}
          >
            {label}
          </button>
        ))}
      </div>
      <div className="flow-canvas">
        <ReactFlow
          key={analysis.id + layer}
          nodes={flowNodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onNodeClick={(_, n) => {
            const item = analysis.graph.nodes.find((item) => item.id === n.id);
            if (item) onSelect(item);
          }}
          fitView
          fitViewOptions={{ padding: 0.17 }}
          minZoom={0.15}
          maxZoom={1.7}
          nodesDraggable
          nodesConnectable={false}
          edgesFocusable={false}
          attributionPosition="bottom-left"
        >
          <Background gap={24} size={1} color="#c7cfc6" />
          <Controls showInteractive={false} />
        </ReactFlow>
      </div>
      <div className="graph-legend">
        {Object.entries(colors).map(([type, color]) => (
          <span key={type}>
            <i style={{ background: color }} />
            {typeNames[type as GraphNode["type"]]}
          </span>
        ))}
        <span className="relation-key">┄ Relação temática</span>
        <span className="relation-key">⟶ Relação documental</span>
      </div>
      <p className="graph-help">
        Selecione um nó para inspecionar. Arraste para navegar e use +/− para
        aproximar. Resultados também disponíveis na lista.
      </p>
    </section>
  );
}
