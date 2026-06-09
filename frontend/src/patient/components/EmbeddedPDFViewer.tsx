import { useCallback, useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { ChevronLeft, ChevronRight, ZoomIn, ZoomOut, Maximize2 } from 'lucide-react';

interface ViewerHighlight {
  id: string;
  position: {
    boundingRect: { x1: number; y1: number; x2: number; y2: number; width: number; height: number; pageNumber: number };
    rects: Array<{ x1: number; y1: number; x2: number; y2: number; width: number; height: number; pageNumber: number }>;
    pageNumber: number;
  };
  comment: {
    text: string;
    query?: string;
  };
}

interface EmbeddedPDFViewerProps {
  fileUrl: string;
  highlights?: ViewerHighlight[];
  activeHighlightId?: string | null;
  onHighlightClick?: (highlightId: string) => void;
}

/**
 * Embedded PDF Viewer with highlight overlays.
 *
 * Uses an <iframe> for the PDF rendering (browser-native PDF viewer)
 * with an overlay layer for highlights. This avoids the heavy PDF.js bundle
 * while still providing page navigation and highlight visualization.
 *
 * For the highlight overlay, we render colored rectangles at the bbox coordinates
 * on a canvas-like layer that sits on top of the PDF.
 */
export function EmbeddedPDFViewer({
  fileUrl,
  highlights = [],
  activeHighlightId,
  onHighlightClick,
}: EmbeddedPDFViewerProps) {
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [zoom, setZoom] = useState(100);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Get highlights for the current page
  const pageHighlights = highlights.filter(
    (h) => h.position.pageNumber === currentPage
  );

  // Jump to a page when activeHighlightId changes
  useEffect(() => {
    if (!activeHighlightId) return;
    const highlight = highlights.find((h) => h.id === activeHighlightId);
    if (highlight) {
      setCurrentPage(highlight.position.pageNumber);
    }
  }, [activeHighlightId, highlights]);

  // Navigate to page via URL fragment (browser PDF viewer supports #page=N)
  const navigateToPage = useCallback(
    (page: number) => {
      setCurrentPage(page);
      if (iframeRef.current) {
        iframeRef.current.src = `${fileUrl}#page=${page}`;
      }
    },
    [fileUrl]
  );

  const handleZoomIn = () => setZoom((z) => Math.min(z + 25, 200));
  const handleZoomOut = () => setZoom((z) => Math.max(z - 25, 50));

  const toggleFullscreen = () => {
    if (!containerRef.current) return;
    if (!document.fullscreenElement) {
      containerRef.current.requestFullscreen().catch(() => {});
      setIsFullscreen(true);
    } else {
      document.exitFullscreen().catch(() => {});
      setIsFullscreen(false);
    }
  };

  return (
    <div
      ref={containerRef}
      className={`relative overflow-hidden rounded-2xl border border-outline-variant/20 bg-surface-container-low ${
        isFullscreen ? 'h-screen' : 'h-[520px]'
      }`}
    >
      {/* Toolbar */}
      <div className="absolute left-0 right-0 top-0 z-10 flex items-center justify-between border-b border-outline-variant/15 bg-surface/90 px-4 py-2 backdrop-blur-md">
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => navigateToPage(Math.max(1, currentPage - 1))}
            className="rounded-lg p-1.5 text-on-surface/60 hover:bg-surface-container-low"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
          <span className="text-xs font-medium text-on-surface/60">Page {currentPage}</span>
          <button
            type="button"
            onClick={() => navigateToPage(currentPage + 1)}
            className="rounded-lg p-1.5 text-on-surface/60 hover:bg-surface-container-low"
          >
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>

        <div className="flex items-center gap-1.5">
          <button
            type="button"
            onClick={handleZoomOut}
            className="rounded-lg p-1.5 text-on-surface/60 hover:bg-surface-container-low"
          >
            <ZoomOut className="h-4 w-4" />
          </button>
          <span className="min-w-[36px] text-center text-[11px] font-medium text-on-surface/50">{zoom}%</span>
          <button
            type="button"
            onClick={handleZoomIn}
            className="rounded-lg p-1.5 text-on-surface/60 hover:bg-surface-container-low"
          >
            <ZoomIn className="h-4 w-4" />
          </button>
          <div className="mx-1.5 h-4 w-px bg-outline-variant/20" />
          <button
            type="button"
            onClick={toggleFullscreen}
            className="rounded-lg p-1.5 text-on-surface/60 hover:bg-surface-container-low"
          >
            <Maximize2 className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* PDF iframe */}
      <iframe
        ref={iframeRef}
        src={`${fileUrl}#page=${currentPage}`}
        title="PDF Viewer"
        className="h-full w-full border-0 pt-10"
        style={{ transform: `scale(${zoom / 100})`, transformOrigin: 'top left', width: `${10000 / zoom}%`, height: `${10000 / zoom}%` }}
      />

      {/* Highlight Overlays */}
      <AnimatePresence>
        {pageHighlights.map((highlight) => {
          const rect = highlight.position.boundingRect;
          const isActive = highlight.id === activeHighlightId;
          return (
            <motion.div
              key={highlight.id}
              initial={{ opacity: 0 }}
              animate={{
                opacity: isActive ? 0.4 : 0.2,
                boxShadow: isActive ? '0 0 12px rgba(26, 115, 232, 0.5)' : 'none',
              }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.3 }}
              onClick={() => onHighlightClick?.(highlight.id)}
              className={`absolute cursor-pointer rounded-sm border-2 transition-all ${
                isActive
                  ? 'border-primary bg-primary/25'
                  : 'border-primary/30 bg-primary/10 hover:border-primary/60 hover:bg-primary/20'
              }`}
              style={{
                left: `${(rect.x1 / 612) * 100}%`,
                top: `${(rect.y1 / 792) * 100 + (10 / 520) * 100}%`,
                width: `${(rect.width / 612) * 100}%`,
                height: `${(rect.height / 792) * 100}%`,
              }}
              title={highlight.comment.text}
            />
          );
        })}
      </AnimatePresence>

      {/* Active highlight pulse indicator */}
      {activeHighlightId && pageHighlights.some((h) => h.id === activeHighlightId) && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: [0.6, 0.2, 0.6] }}
          transition={{ duration: 2, repeat: Infinity }}
          className="pointer-events-none absolute inset-0 rounded-2xl border-2 border-primary/30"
        />
      )}
    </div>
  );
}
