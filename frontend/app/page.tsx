"use client";

import { useState } from "react";
import { generateConfig } from "@/lib/api";
import { GenerateResponse } from "@/lib/types";
import PipelineTrace from "@/components/PipelineTrace";
import JsonOutputViewer from "@/components/JsonOutputViewer";
import ValidationPanel from "@/components/ValidationPanel";
import RuntimePanel from "@/components/RuntimePanel";
import AssumptionsPanel from "@/components/AssumptionsPanel";

export default function Home() {
  const [prompt, setPrompt] = useState("");
  const [mode, setMode] = useState<"fast" | "quality">("quality");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<GenerateResponse | null>(null);
  const [error, setError] = useState("");

  const handleGenerate = async () => {
    if (!prompt.trim()) return;
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const res = await generateConfig(prompt, mode);
      setResult(res);
    } catch (err: any) {
      setError(err.message || "Failed to generate");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen p-8 max-w-7xl mx-auto">
      <header className="mb-8">
        <h1 className="text-4xl font-extrabold tracking-tight text-slate-900">ConfigForge AI</h1>
        <p className="text-lg text-slate-600 mt-2">Compiler-style AI app configuration generator</p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-1 space-y-6">
          <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
            <label className="block text-sm font-medium mb-2 text-slate-700">App Description Prompt</label>
            <textarea 
              className="w-full h-32 p-3 border border-slate-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:outline-none"
              placeholder="Build a CRM with login, contacts, dashboard..."
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
            />
            
            <div className="mt-4 flex items-center justify-between">
              <div className="flex space-x-2">
                <button 
                  onClick={() => setMode("fast")}
                  className={`px-4 py-2 text-sm rounded-md transition-colors ${mode === "fast" ? "bg-slate-800 text-white" : "bg-slate-100 text-slate-700 hover:bg-slate-200"}`}
                >
                  Fast Mode
                </button>
                <button 
                  onClick={() => setMode("quality")}
                  className={`px-4 py-2 text-sm rounded-md transition-colors ${mode === "quality" ? "bg-slate-800 text-white" : "bg-slate-100 text-slate-700 hover:bg-slate-200"}`}
                >
                  Quality Mode
                </button>
              </div>
              <button 
                onClick={handleGenerate}
                disabled={loading || !prompt.trim()}
                className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md font-medium disabled:opacity-50 transition-colors"
              >
                {loading ? "Compiling..." : "Generate"}
              </button>
            </div>
          </div>

          {error && <div className="p-4 bg-red-50 text-red-700 border border-red-200 rounded-md">{error}</div>}

          {result && (
            <>
              <PipelineTrace trace={result.final_config.pipeline_trace} />
              <AssumptionsPanel assumptions={result.final_config.intent.assumptions} warnings={result.final_config.metadata.warnings} />
            </>
          )}
        </div>

        <div className="lg:col-span-2 space-y-6">
          {result ? (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <ValidationPanel report={result.validation_report} repair={result.repair_report} />
                <RuntimePanel report={result.runtime_report} />
              </div>
              <JsonOutputViewer data={result.final_config} />
            </>
          ) : (
            <div className="h-full flex flex-col items-center justify-center border-2 border-dashed border-slate-200 rounded-xl bg-slate-50 text-slate-400 p-12">
              <svg className="w-16 h-16 mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"></path></svg>
              <p>Enter a prompt and generate to see the compiler pipeline in action.</p>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
