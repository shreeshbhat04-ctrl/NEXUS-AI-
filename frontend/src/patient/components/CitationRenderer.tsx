import { useMemo } from 'react';
import { CitationMarker } from './CitationMarker';
import type { FinancePolicyCitation } from '../../shared/lib/api';

interface CitationRendererProps {
  /** The text containing [1], [2] markers to be rendered with interactive citation components. */
  text: string;
  /** The citations array — marker [N] maps to citations[N-1]. */
  citations: FinancePolicyCitation[];
  /** Currently active citation ID (highlighted). */
  activeCitationId: string | null;
  /** Called when a citation marker is clicked. */
  onCitationClick: (citationId: string) => void;
  /** Called when a citation should jump the PDF viewer to a page. */
  onJumpToPage?: (page: number, citationId: string) => void;
}

/**
 * Parses text containing [N] markers and replaces them with interactive
 * CitationMarker components that show popovers on hover.
 *
 * Example:
 *   Input:  "MRI covered up to ₹15,000 [1] per policy year [2]"
 *   Output: <span>MRI covered up to ₹15,000 <CitationMarker index={1}/> per policy year <CitationMarker index={2}/></span>
 */
export function CitationRenderer({
  text,
  citations,
  activeCitationId,
  onCitationClick,
  onJumpToPage,
}: CitationRendererProps) {
  const segments = useMemo(() => {
    // Split on [N] patterns, capturing the number
    const parts = text.split(/\[(\d+)\]/g);
    const result: Array<{ type: 'text'; content: string } | { type: 'citation'; index: number }> = [];

    for (let i = 0; i < parts.length; i++) {
      if (i % 2 === 0) {
        // Text segment
        if (parts[i]) {
          result.push({ type: 'text', content: parts[i] });
        }
      } else {
        // Number segment (captured group)
        result.push({ type: 'citation', index: parseInt(parts[i], 10) });
      }
    }

    return result;
  }, [text]);

  return (
    <span className="citation-rendered-text">
      {segments.map((segment, i) => {
        if (segment.type === 'text') {
          return <span key={i}>{segment.content}</span>;
        }

        // Citation marker — index is 1-based, citations array is 0-based
        const citation = citations[segment.index - 1];
        if (!citation) {
          // If no matching citation, render the raw marker
          return <span key={i}>[{segment.index}]</span>;
        }

        return (
          <CitationMarker
            key={`${citation.id}-${i}`}
            index={segment.index}
            citation={citation}
            isActive={activeCitationId === citation.id}
            onActivate={onCitationClick}
            onJumpToPage={onJumpToPage}
          />
        );
      })}
    </span>
  );
}
