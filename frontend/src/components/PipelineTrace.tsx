import React from "react";
import { StageTrace } from "@/lib/types";

export default function PipelineTrace({ trace }: { trace: StageTrace[] }) {
  return (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
      <h3 className="text-lg font-semibold mb-4 text-slate-800">Pipeline Trace</h3>
      <div className="space-y-4 relative">
        <div className="absolute left-3 top-2 bottom-2 w-0.5 bg-slate-200" />
        {trace.map((stage, i) => (
          <div key={i} className="relative flex items-start pl-8">
            <div className={`absolute left-2 w-2.5 h-2.5 rounded-full mt-1.5 ${
              stage.status === 'success' ? 'bg-green-500' :
              stage.status === 'repaired' ? 'bg-yellow-500' : 'bg-red-500'
            }`} />
            <div>
              <p className="font-medium text-slate-800">{stage.stage}</p>
              <p className="text-xs text-slate-500 mt-1">
                {stage.latency_ms}ms • {stage.status.toUpperCase()}
                {stage.repair_attempts > 0 && ` • ${stage.repair_attempts} repairs`}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
