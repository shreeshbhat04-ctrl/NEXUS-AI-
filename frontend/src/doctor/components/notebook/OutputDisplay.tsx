export default function OutputDisplay({ output }: { output: any }) {
  if (!output) return null;

  return (
    <div 
      style={{
        marginTop: '1rem',
        padding: '1rem',
        backgroundColor: '#ffffff',
        borderRadius: '0.5rem',
        border: '1px solid #e2e8f0',
        boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)'
      }}
    >
      <h3 
        style={{
          fontSize: '0.875rem',
          fontWeight: 600,
          color: '#64748b',
          marginBottom: '0.75rem',
          textTransform: 'uppercase',
          letterSpacing: '0.05em'
        }}
      >
        Output
      </h3>
      
      {/* Stdout Logs */}
      {output.logs && output.logs.stdout && output.logs.stdout.length > 0 && (
        <div 
          style={{
            backgroundColor: '#f8fafc',
            padding: '0.75rem',
            borderRadius: '0.25rem',
            fontSize: '0.875rem',
            fontFamily: 'monospace',
            whiteSpace: 'pre-wrap',
            color: '#334155',
            border: '1px solid #f1f5f9',
            marginBottom: '0.75rem'
          }}
        >
          {output.logs.stdout.join("")}
        </div>
      )}

      {/* Text property if present */}
      {output.text && (
         <div 
           style={{
             backgroundColor: '#f8fafc',
             padding: '0.75rem',
             borderRadius: '0.25rem',
             fontSize: '0.875rem',
             fontFamily: 'monospace',
             whiteSpace: 'pre-wrap',
             color: '#334155',
             border: '1px solid #f1f5f9',
             marginBottom: '0.75rem'
           }}
         >
           {output.text}
         </div>
      )}

      {/* Errors */}
      {output.error && (
        <div 
          style={{
            backgroundColor: '#fef2f2',
            padding: '0.75rem',
            borderRadius: '0.25rem',
            fontSize: '0.875rem',
            fontFamily: 'monospace',
            whiteSpace: 'pre-wrap',
            color: '#dc2626',
            border: '1px solid #fee2e2',
            marginBottom: '0.75rem'
          }}
        >
          <span style={{ fontWeight: 'bold' }}>{output.error.name}: </span>
          {output.error.value}
          {output.error.traceback && (
            <div style={{ marginTop: '0.5rem', fontSize: '0.75rem', opacity: 0.8 }}>
              {output.error.traceback}
            </div>
          )}
        </div>
      )}

      {/* Visual Results (Plots/Charts) */}
      {output.results && output.results.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginTop: '0.75rem' }}>
          {output.results.map((res: any, idx: number) => {
            if (res.png) {
              return (
                <img 
                  key={idx} 
                  src={`data:image/png;base64,${res.png}`} 
                  alt="Output plot" 
                  style={{
                    borderRadius: '0.5rem',
                    boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
                    maxWidth: '100%',
                    border: '1px solid #e2e8f0'
                  }} 
                />
              );
            } else if (res.jpeg) {
              return (
                <img 
                  key={idx} 
                  src={`data:image/jpeg;base64,${res.jpeg}`} 
                  alt="Output plot" 
                  style={{
                    borderRadius: '0.5rem',
                    boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
                    maxWidth: '100%',
                    border: '1px solid #e2e8f0'
                  }} 
                />
              );
            } else if (res.svg) {
              return (
                <div 
                  key={idx} 
                  dangerouslySetInnerHTML={{ __html: res.svg }} 
                  style={{ backgroundColor: '#ffffff', padding: '0.5rem', borderRadius: '0.5rem' }} 
                />
              );
            } else if (res.html) {
               return (
                 <div 
                   key={idx} 
                   dangerouslySetInnerHTML={{ __html: res.html }} 
                   style={{ backgroundColor: '#ffffff', padding: '0.5rem', borderRadius: '0.5rem' }} 
                 />
               );
            }
            return null;
          })}
        </div>
      )}
      
      {!output.text && (!output.logs?.stdout?.length) && (!output.results?.length) && !output.error && (
        <div style={{ color: '#94a3b8', fontStyle: 'italic', fontSize: '0.875rem' }}>
          Execution finished with no output.
        </div>
      )}
    </div>
  );
}
