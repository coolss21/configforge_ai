"use client";

import { useState } from "react";
import { evaluateSystem } from "@/lib/api";

export default function EvaluationPage() {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState("");

  const handleRun = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await evaluateSystem();
      setData(res);
    } catch (err: any) {
      setError(err.message || "Evaluation failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen p-8 max-w-7xl mx-auto">
      <header className="mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-4xl font-extrabold tracking-tight text-slate-900">Evaluation Dashboard</h1>
          <p className="text-lg text-slate-600 mt-2">Benchmark metrics for ConfigForge AI</p>
        </div>
        <button 
          onClick={handleRun}
          disabled={loading}
          className="px-6 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-md font-medium disabled:opacity-50 transition-colors"
        >
          {loading ? "Running Benchmark..." : "Run Benchmark"}
        </button>
      </header>

      {error && <div className="p-4 bg-red-50 text-red-700 mb-8 border border-red-200 rounded-md">{error}</div>}

      {data && (
        <div className="space-y-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
              <p className="text-sm font-medium text-slate-500 mb-1">Total Prompts</p>
              <p className="text-3xl font-bold text-slate-900">{data.summary.total_prompts}</p>
            </div>
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
              <p className="text-sm font-medium text-slate-500 mb-1">Success Rate</p>
              <p className="text-3xl font-bold text-green-600">{(data.summary.success_rate * 100).toFixed(0)}%</p>
            </div>
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
              <p className="text-sm font-medium text-slate-500 mb-1">Executable Rate</p>
              <p className="text-3xl font-bold text-blue-600">{(data.summary.runtime_executable_rate * 100).toFixed(0)}%</p>
            </div>
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
              <p className="text-sm font-medium text-slate-500 mb-1">Avg Repairs</p>
              <p className="text-3xl font-bold text-slate-900">{data.summary.average_repair_attempts.toFixed(1)}</p>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
            <table className="w-full text-sm text-left">
              <thead className="bg-slate-50 text-slate-600 font-medium border-b border-slate-200">
                <tr>
                  <th className="px-6 py-4">Prompt ID</th>
                  <th className="px-6 py-4">Type</th>
                  <th className="px-6 py-4">Success</th>
                  <th className="px-6 py-4">Runtime</th>
                  <th className="px-6 py-4">Repairs</th>
                  <th className="px-6 py-4">Latency</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {data.results.map((res: any, idx: number) => (
                  <tr key={idx} className="hover:bg-slate-50">
                    <td className="px-6 py-4 font-medium text-slate-900">{res.prompt_id}</td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 text-xs rounded-full ${res.prompt_type === 'normal' ? 'bg-blue-100 text-blue-700' : 'bg-orange-100 text-orange-700'}`}>
                        {res.prompt_type}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      {res.success ? <span className="text-green-600 font-medium">Yes</span> : <span className="text-red-600 font-medium">No</span>}
                    </td>
                    <td className="px-6 py-4">
                      {res.runtime_executable ? <span className="text-green-600 font-medium">Yes</span> : <span className="text-red-600 font-medium">No</span>}
                    </td>
                    <td className="px-6 py-4">{res.repair_attempts}</td>
                    <td className="px-6 py-4">{res.latency_ms}ms</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </main>
  );
}
