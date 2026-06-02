import { useState } from "react";
import Editor from "@monaco-editor/react";
import { Play, Loader2, Bot, MessageSquare } from "lucide-react";
import SmilesRenderer from "./SmilesRenderer";
import OutputDisplay from "./OutputDisplay";
import type { CellData } from "../../lib/types";
import "./notebook.css";

type CellProps = {
  cell: CellData;
  onChange: (id: string, code: string) => void;
  onRun: (id: string, code: string) => void;
  onChat: (id: string, code: string, message: string) => Promise<void>;
};

export default function Cell({ cell, onChange, onRun, onChat }: CellProps) {
  const [prompt, setPrompt] = useState("");
  const [isChatting, setIsChatting] = useState(false);

  const handleRun = () => {
    onRun(cell.id, cell.code);
  };

  const handleChat = async () => {
    if (!prompt.trim()) return;
    setIsChatting(true);
    await onChat(cell.id, cell.code, prompt);
    setIsChatting(false);
    setPrompt("");
  };

  const renderOutput = () => {
    if (cell.isLoading) {
      return (
        <div style={{ color: '#3b82f6', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Loader2 size={16} className="animate-spin"/> Executing...
        </div>
      );
    }
    
    if (cell.errors) {
      return <pre style={{ color: '#dc2626', whiteSpace: 'pre-wrap', fontFamily: 'monospace' }}>{cell.errors}</pre>;
    }

    if (typeof cell.output === "string" && cell.output) {
      try {
        const parsed = JSON.parse(cell.output);
        if (parsed.type === "smiles") {
          return <SmilesRenderer smiles={parsed.data} />;
        }
      } catch {
        // Not JSON or not smiles, normal string
      }
      return <pre style={{ color: '#334155', whiteSpace: 'pre-wrap', fontFamily: 'monospace' }}>{cell.output}</pre>;
    }

    if (cell.output) {
      return <OutputDisplay output={cell.output} />;
    }
    
    return null;
  };

  return (
    <div className="notebook-cell">
      {/* Editor Header & Run Button */}
      <div className="notebook-cell-header">
        <span className="notebook-cell-title">Python Cell</span>
        <button 
          onClick={handleRun}
          disabled={cell.isLoading}
          className="btn-run"
        >
          {cell.isLoading ? <Loader2 size={16} className="animate-spin" /> : <Play size={16} />}
          Run
        </button>
      </div>

      {/* Monaco Editor */}
      <div className="editor-container">
        <Editor
          height="100%"
          language="python"
          value={cell.code}
          onChange={(val) => onChange(cell.id, val || "")}
          options={{ minimap: { enabled: false }, fontSize: 14 }}
        />
      </div>

      {/* Output Area */}
      {(cell.output || cell.errors || cell.isLoading) && (
        <div className="output-container">
          {renderOutput()}
        </div>
      )}

      {/* Agent Chat Area for this specific cell */}
      <div className="agent-area">
        {cell.agentResponse && (
          <div className="agent-response-box">
            <Bot size={20} className="agent-avatar" />
            <div className="agent-text">{cell.agentResponse}</div>
          </div>
        )}
        
        <div className="chat-input-row">
          <input 
            type="text" 
            placeholder="Ask medical copilot to explain or modify this code..." 
            className="chat-input"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleChat()}
          />
          <button 
            onClick={handleChat}
            disabled={isChatting || !prompt.trim()}
            className="btn-chat-send"
          >
            {isChatting ? <Loader2 size={18} className="animate-spin" /> : <MessageSquare size={18} />}
          </button>
        </div>
      </div>
    </div>
  );
}
