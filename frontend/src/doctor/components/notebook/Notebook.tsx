import { useState, useEffect, useRef } from "react";
import Cell from "./Cell";
import type { CellData } from "../../lib/types";
import { Plus, Sparkles, AlertCircle, Loader2 } from "lucide-react";
import { runCell, chatNotebook, explainOptions } from "../../lib/doctorApi";
import mermaid from "mermaid";
import "./notebook.css";

// Initialize mermaid
mermaid.initialize({
  startOnLoad: false,
  theme: 'neutral',
  securityLevel: 'loose',
});

// Mermaid component
function MermaidDiagram({ chart }: { chart: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const [svg, setSvg] = useState<string>("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!chart) return;
    
    const renderChart = async () => {
      try {
        setError(null);
        const id = `mermaid-${Math.floor(Math.random() * 1000000)}`;
        const { svg: renderedSvg } = await mermaid.render(id, chart);
        setSvg(renderedSvg);
      } catch (err: any) {
        console.error("Mermaid render error", err);
        setError("Could not render decision flow diagram.");
        // Clear badge from body if mermaid injected it on failure
        const badEl = document.getElementById(`d${chart}`);
        if (badEl) badEl.remove();
      }
    };

    renderChart();
  }, [chart]);

  if (error) {
    return <div style={{ fontSize: '0.75rem', color: '#dc2626', fontStyle: 'italic' }}>{error}</div>;
  }

  if (!svg) {
    return <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.75rem', color: '#64748b' }}><Loader2 size={12} className="animate-spin" /> Rendering diagram...</div>;
  }

  return <div dangerouslySetInnerHTML={{ __html: svg }} />;
}

export default function Notebook({ sandboxId, setSandboxId }: { sandboxId: string | null, setSandboxId: (id: string) => void }) {
  const [cells, setCells] = useState<CellData[]>([
    { id: "1", code: "# Write some python here\nimport pandas as pd\nimport numpy as np\nprint('Hello Medical AI Notebook initialized!')", output: null, errors: null, isLoading: false, agentResponse: null }
  ]);
  
  // General copilot prompt state
  const [copilotPrompt, setCopilotPrompt] = useState("");
  const [isCopilotLoading, setIsCopilotLoading] = useState(false);
  
  // Ambiguity state
  const [ambiguousData, setAmbiguousData] = useState<{
    question: string;
    options: string[];
    mermaidCode?: string;
  } | null>(null);
  const [isGeneratingDiagram, setIsGeneratingDiagram] = useState(false);

  const addCell = (code = "", output = null) => {
    setCells((prev) => [
      ...prev,
      { id: Date.now().toString(), code, output, errors: null, isLoading: false, agentResponse: null },
    ]);
  };

  const updateCellCode = (id: string, code: string) => {
    setCells((prev) => prev.map((cell) => (cell.id === id ? { ...cell, code } : cell)));
  };

  const handleRun = async (id: string, code: string) => {
    setCells((prev) =>
      prev.map((cell) =>
        cell.id === id ? { ...cell, isLoading: true, output: null, errors: null } : cell
      )
    );
    
    try {
      const data = await runCell(code, "", sandboxId);

      if (data.sandboxId) {
        setSandboxId(data.sandboxId);
      }

      setCells((prev) =>
        prev.map((cell) =>
          cell.id === id
            ? {
                ...cell,
                isLoading: false,
                output: data.result ?? null,
                errors: data.errors ?? null,
              }
            : cell
        )
      );
    } catch (e: any) {
      setCells((prev) =>
        prev.map((cell) =>
          cell.id === id ? { ...cell, isLoading: false, errors: e.message } : cell
        )
      );
    }
  };

  const handleChat = async (id: string, code: string, message: string) => {
    try {
      const data = await chatNotebook(message, code);
      setCells((prev) =>
        prev.map((cell) => (cell.id === id ? { ...cell, agentResponse: data.response } : cell))
      );
    } catch (e: any) {
      setCells((prev) =>
        prev.map((cell) =>
          cell.id === id ? { ...cell, agentResponse: `Error: ${e.message}` } : cell
        )
      );
    }
  };

  // Submit global prompt to generate new cells
  const handleCopilotSubmit = async (overridePrompt?: string) => {
    const activePrompt = overridePrompt || copilotPrompt;
    if (!activePrompt.trim()) return;
    
    setIsCopilotLoading(true);
    setAmbiguousData(null);
    
    try {
      const data = await runCell("", activePrompt, sandboxId);
      
      if (data.sandboxId) {
        setSandboxId(data.sandboxId);
      }
      
      if (data.status === "AMBIGUOUS") {
        // Medical copilot needs clarification
        setIsGeneratingDiagram(true);
        try {
          const diagramRes = await explainOptions(data.question, data.options);
          setAmbiguousData({
            question: data.question,
            options: data.options,
            mermaidCode: diagramRes.mermaid
          });
        } catch {
          setAmbiguousData({
            question: data.question,
            options: data.options
          });
        } finally {
          setIsGeneratingDiagram(false);
        }
      } else {
        // EXECUTABLE
        addCell(data.code, data.result);
        setCopilotPrompt("");
      }
    } catch (err: any) {
      alert("Error generating code: " + err.message);
    } finally {
      setIsCopilotLoading(false);
    }
  };

  return (
    <div className="notebook-container">
      {/* Premium Copilot Section */}
      <div 
        style={{
          padding: '1.25rem',
          background: 'linear-gradient(135deg, #eff6ff 0%, #f5f3ff 100%)',
          border: '1px solid #dbeafe',
          borderRadius: '1rem',
          marginBottom: '1rem'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#1d4ed8', fontWeight: 600, marginBottom: '0.75rem' }}>
          <Sparkles size={18} />
          <h2 style={{ fontSize: '1rem', margin: 0 }}>Gemini Medical Copilot</h2>
        </div>
        <p style={{ fontSize: '0.85rem', color: '#475569', margin: '0 0 1rem 0' }}>
          Explain your analysis target in plain language. The Copilot will generate executable medical code to plot patient charts, verify drug safety, or format diagnostic datasets.
        </p>
        
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <input 
            type="text"
            placeholder="e.g., plot the patient's heart rate over the last 3 hours..."
            style={{
              flex: 1,
              padding: '0.75rem 1rem',
              borderRadius: '0.5rem',
              border: '1px solid #cbd5e1',
              backgroundColor: '#ffffff',
              fontSize: '0.875rem',
              outline: 'none'
            }}
            value={copilotPrompt}
            onChange={(e) => setCopilotPrompt(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleCopilotSubmit()}
            disabled={isCopilotLoading}
          />
          <button
            onClick={() => handleCopilotSubmit()}
            disabled={isCopilotLoading || !copilotPrompt.trim()}
            style={{
              backgroundColor: '#2563eb',
              color: '#ffffff',
              padding: '0.75rem 1.25rem',
              borderRadius: '0.5rem',
              fontWeight: 500,
              fontSize: '0.875rem',
              border: 'none',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}
          >
            {isCopilotLoading ? <Loader2 size={16} className="animate-spin" /> : <Sparkles size={16} />}
            Generate
          </button>
        </div>

        {/* Clarification interface */}
        {ambiguousData && (
          <div 
            style={{
              marginTop: '1.25rem',
              padding: '1rem',
              backgroundColor: '#ffffff',
              border: '1px solid #e2e8f0',
              borderRadius: '0.75rem',
              display: 'flex',
              flexDirection: 'column',
              gap: '1rem'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.5rem', color: '#d97706' }}>
              <AlertCircle size={18} style={{ flexShrink: 0, marginTop: '0.1rem' }} />
              <div>
                <h3 style={{ fontSize: '0.9rem', fontWeight: 600, margin: 0 }}>Clarification Needed</h3>
                <p style={{ fontSize: '0.85rem', color: '#475569', margin: '0.25rem 0 0 0' }}>{ambiguousData.question}</p>
              </div>
            </div>

            {/* Decision flow chart */}
            {ambiguousData.mermaidCode && (
              <div 
                style={{
                  padding: '1rem',
                  backgroundColor: '#f8fafc',
                  border: '1px solid #e2e8f0',
                  borderRadius: '0.5rem',
                  display: 'flex',
                  justifyContent: 'center',
                  overflowX: 'auto'
                }}
              >
                <MermaidDiagram chart={ambiguousData.mermaidCode} />
              </div>
            )}

            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
              {ambiguousData.options.map((opt, i) => (
                <button
                  key={i}
                  onClick={() => {
                    const promptText = `Regarding "${ambiguousData.question}": I choose option: ${opt}`;
                    setCopilotPrompt(promptText);
                    handleCopilotSubmit(promptText);
                  }}
                  style={{
                    backgroundColor: '#f1f5f9',
                    color: '#1e293b',
                    border: '1px solid #e2e8f0',
                    padding: '0.5rem 1rem',
                    borderRadius: '0.375rem',
                    fontSize: '0.8rem',
                    fontWeight: 500,
                    cursor: 'pointer',
                    transition: 'all 0.2s'
                  }}
                  onMouseOver={(e) => {
                    e.currentTarget.style.backgroundColor = '#e2e8f0';
                  }}
                  onMouseOut={(e) => {
                    e.currentTarget.style.backgroundColor = '#f1f5f9';
                  }}
                >
                  {opt}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Cells List */}
      {cells.map((cell) => (
        <Cell 
          key={cell.id} 
          cell={cell} 
          onChange={updateCellCode} 
          onRun={handleRun}
          onChat={handleChat}
        />
      ))}
      
      <button 
        onClick={() => addCell()}
        className="btn-add-cell"
      >
        <Plus size={20} />
        Add Python Cell
      </button>
    </div>
  );
}
