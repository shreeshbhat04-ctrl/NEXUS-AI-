import { useEffect, useRef } from 'react';

export default function SmilesRenderer({ smiles }: { smiles: string }) {
  const viewerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Dynamically load 3Dmol.js if not present
    if (!window.$3Dmol) {
      const script = document.createElement('script');
      script.src = "https://3dmol.org/build/3Dmol-min.js";
      script.onload = initViewer;
      document.head.appendChild(script);
    } else {
      initViewer();
    }

    function initViewer() {
      if (!viewerRef.current) return;
      viewerRef.current.innerHTML = '';
      
      const config = { backgroundColor: '#f8fafc' };
      const viewer = window.$3Dmol.createViewer(viewerRef.current, config);
      
      // If it's a raw smiles, we can fetch the SDF from PubChem:
      if (!smiles.includes('\n')) {
        fetch(`https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/smiles/${encodeURIComponent(smiles)}/SDF`)
          .then(res => res.text())
          .then(sdf => {
            viewer.addModel(sdf, "sdf");
            viewer.setStyle({}, { stick: {} });
            viewer.zoomTo();
            viewer.render();
          })
          .catch(err => {
            console.error("Failed to load SMILES from PubChem", err);
          });
      } else {
        // It's a mol block
        viewer.addModel(smiles, "sdf");
        viewer.setStyle({}, { stick: {} });
        viewer.zoomTo();
        viewer.render();
      }
    }
  }, [smiles]);

  return (
    <div 
      style={{
        width: '100%',
        height: '400px',
        backgroundColor: '#f8fafc',
        border: '1px solid #e2e8f0',
        borderRadius: '0.5rem',
        position: 'relative',
        overflow: 'hidden'
      }} 
      ref={viewerRef}
    >
      <div 
        style={{
          position: 'absolute',
          top: '0.5rem',
          left: '0.5rem',
          backgroundColor: 'rgba(255, 255, 255, 0.8)',
          padding: '0.25rem 0.5rem',
          fontSize: '0.75rem',
          borderRadius: '0.25rem',
          boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
          zIndex: 10,
          color: '#64748b',
          fontFamily: 'monospace'
        }}
      >
        3Dmol.js Viewer
      </div>
    </div>
  );
}

// Add TS definition for window.$3Dmol
declare global {
  interface Window {
    $3Dmol: any;
  }
}
