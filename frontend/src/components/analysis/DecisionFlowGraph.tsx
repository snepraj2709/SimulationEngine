import { useMemo } from "react";
import ReactFlow, { Background, Controls, Edge, MarkerType, Node } from "react-flow-renderer";
import "react-flow-renderer/dist/style.css";

import { AnalysisDetail, Scenario, SimulationRun } from "@/types/api";

interface DecisionFlowGraphProps {
  analysis: AnalysisDetail;
  scenario: Scenario;
  run?: SimulationRun;
  selectedICPId?: string | null;
}

export function DecisionFlowGraph({
  analysis,
  scenario,
  run,
  selectedICPId,
}: DecisionFlowGraphProps) {
  const { nodes, edges } = useMemo(() => {
    if (!run) return { nodes: [] as Node[], edges: [] as Edge[] };

    const builtNodes: Node[] = [];
    const builtEdges: Edge[] = [];

    run.results.forEach((result, index) => {
      const icp = analysis.icp_profiles.find((profile) => profile.id === result.icp_profile_id);
      if (!icp) return;
      const y = index * 180;
      const highlight = icp.id === selectedICPId;

      builtNodes.push({
        id: `icp-${icp.id}`,
        position: { x: 0, y },
        data: { label: `${icp.name}\n${(icp.segment_weight * 100).toFixed(0)}% weight` },
        style: {
          width: 240,
          borderRadius: 18,
          border: highlight ? "2px solid #0f172a" : "1px solid #cbd5e1",
          background: highlight ? "#f8fafc" : "#ffffff",
          padding: 12,
          fontSize: 12,
          whiteSpace: "pre-line",
        },
      });

      const impacts = Object.entries(result.driver_impacts_json)
        .sort((left, right) => Math.abs(right[1]) - Math.abs(left[1]))
        .slice(0, 2);

      impacts.forEach(([driver, impact], impactIndex) => {
        const driverNodeId = `driver-${icp.id}-${driver}`;
        builtNodes.push({
          id: driverNodeId,
          position: { x: 310, y: y + impactIndex * 80 },
          data: { label: `${driver.replaceAll("_", " ")} ${impact > 0 ? "+" : ""}${impact.toFixed(2)}` },
          style: {
            width: 200,
            borderRadius: 18,
            border: "1px solid #cbd5e1",
            background: impact >= 0 ? "#ecfeff" : "#fef2f2",
            padding: 12,
            fontSize: 12,
          },
        });
        builtEdges.push({
          id: `edge-icp-${icp.id}-${driver}`,
          source: `icp-${icp.id}`,
          target: driverNodeId,
          markerEnd: { type: MarkerType.ArrowClosed },
          label: "driver shift",
          animated: highlight,
        });
      });

      builtNodes.push({
        id: `reaction-${icp.id}`,
        position: { x: 610, y },
        data: { label: `${result.reaction.toUpperCase()}\nΔ ${result.delta_score.toFixed(2)}` },
        style: {
          width: 170,
          borderRadius: 18,
          border: "1px solid #94a3b8",
          background:
            result.reaction === "churn"
              ? "#fee2e2"
              : result.reaction === "downgrade"
                ? "#fef3c7"
                : result.reaction === "upgrade"
                  ? "#dbeafe"
                  : "#dcfce7",
          padding: 12,
          fontSize: 12,
          fontWeight: 700,
          whiteSpace: "pre-line",
        },
      });
      const primaryImpact = impacts[0]?.[0];
      if (primaryImpact) {
        builtEdges.push({
          id: `edge-reaction-${icp.id}`,
          source: `driver-${icp.id}-${primaryImpact}`,
          target: `reaction-${icp.id}`,
          markerEnd: { type: MarkerType.ArrowClosed },
          label: scenario.scenario_type.replaceAll("_", " "),
        });
      }
    });

    return { nodes: builtNodes, edges: builtEdges };
  }, [analysis.icp_profiles, run, scenario.scenario_type, selectedICPId]);

  return (
    <section className="panel overflow-hidden">
      <div className="panel-header">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Decision Flow</p>
          <h2 className="mt-2 text-2xl font-semibold text-slate-950">How each ICP moves through the simulation</h2>
        </div>
      </div>
      <div className="h-[560px]">
        {run ? (
          <ReactFlow nodes={nodes} edges={edges} fitView minZoom={0.2}>
            <Background color="#e2e8f0" gap={24} />
            <Controls />
          </ReactFlow>
        ) : (
          <div className="flex h-full items-center justify-center text-sm text-slate-500">
            Run or select a scenario to render the reasoning graph.
          </div>
        )}
      </div>
    </section>
  );
}
