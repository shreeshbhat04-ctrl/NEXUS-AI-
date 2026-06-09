import { useState, useRef, useCallback } from 'react';
import {
  useFloating,
  autoUpdate,
  offset,
  flip,
  shift,
  useHover,
  useFocus,
  useDismiss,
  useRole,
  useInteractions,
  FloatingPortal,
} from '@floating-ui/react';
import { motion, AnimatePresence } from 'motion/react';
import { FileText, ExternalLink } from 'lucide-react';
import type { FinancePolicyCitation } from '../../shared/lib/api';

const TAG_COLORS: Record<string, string> = {
  coverage: 'bg-[#e6f4ea] text-[#137333]',
  exclusion: 'bg-[#fce8e6] text-[#c5221f]',
  limitation: 'bg-[#fef7e0] text-[#b06000]',
  general: 'bg-[#e8f0fe] text-[#1a73e8]',
};

interface CitationMarkerProps {
  index: number;
  citation: FinancePolicyCitation;
  isActive: boolean;
  onActivate: (citationId: string) => void;
  onJumpToPage?: (page: number, citationId: string) => void;
}

export function CitationMarker({ index, citation, isActive, onActivate, onJumpToPage }: CitationMarkerProps) {
  const [isOpen, setIsOpen] = useState(false);

  const { refs, floatingStyles, context } = useFloating({
    open: isOpen,
    onOpenChange: setIsOpen,
    placement: 'top',
    middleware: [offset(8), flip(), shift({ padding: 8 })],
    whileElementsMounted: autoUpdate,
  });

  const hover = useHover(context, { move: false, delay: { open: 150, close: 100 } });
  const focus = useFocus(context);
  const dismiss = useDismiss(context);
  const role = useRole(context, { role: 'tooltip' });
  const { getReferenceProps, getFloatingProps } = useInteractions([hover, focus, dismiss, role]);

  const handleClick = useCallback(() => {
    onActivate(citation.id);
    if (onJumpToPage && citation.page_number) {
      onJumpToPage(citation.page_number, citation.id);
    }
    setIsOpen(false);
  }, [citation, onActivate, onJumpToPage]);

  const tagColor = TAG_COLORS[citation.relevance_tag] ?? TAG_COLORS.general;

  return (
    <>
      <sup
        ref={refs.setReference}
        {...getReferenceProps()}
        onClick={handleClick}
        className={`citation-marker relative -top-1 mx-[1px] inline-flex h-[18px] w-[18px] cursor-pointer items-center justify-center rounded-full text-[10px] font-bold leading-none transition-all ${
          isActive
            ? 'bg-primary text-white shadow-[0_0_8px_rgba(26,115,232,0.5)]'
            : 'bg-primary-fixed/50 text-primary hover:bg-primary hover:text-white hover:shadow-[0_0_6px_rgba(26,115,232,0.35)]'
        }`}
      >
        {index}
      </sup>

      <FloatingPortal>
        <AnimatePresence>
          {isOpen && (
            <motion.div
              ref={refs.setFloating}
              style={floatingStyles}
              {...getFloatingProps()}
              initial={{ opacity: 0, y: 4, scale: 0.97 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 4, scale: 0.97 }}
              transition={{ duration: 0.15 }}
              className="z-50 w-[320px] rounded-2xl border border-outline-variant/20 bg-surface/95 p-4 shadow-xl backdrop-blur-xl"
            >
              {/* Header */}
              <div className="flex items-center gap-2 text-xs font-medium text-on-surface/60">
                <FileText className="h-3.5 w-3.5 text-primary/70" />
                <span className="truncate">{citation.section_title}</span>
                <span className={`ml-auto inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${tagColor}`}>
                  {citation.relevance_tag}
                </span>
              </div>

              {/* Excerpt */}
              <p className="mt-2.5 text-[13px] leading-[1.6] text-on-surface/80">
                "{citation.excerpt.length > 200 ? citation.excerpt.slice(0, 200) + '…' : citation.excerpt}"
              </p>

              {/* Footer */}
              <div className="mt-3 flex items-center justify-between">
                <span className="inline-flex items-center gap-1 rounded-full bg-surface-container-low px-2.5 py-1 text-[11px] font-semibold text-on-surface/55">
                  Page {citation.page_number}
                </span>
                <button
                  type="button"
                  onClick={handleClick}
                  className="inline-flex items-center gap-1 text-[11px] font-semibold text-primary hover:underline"
                >
                  Jump to page <ExternalLink className="h-3 w-3" />
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </FloatingPortal>
    </>
  );
}
