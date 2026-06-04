import { useDeferredValue, useMemo, useState } from 'react';
import { BookOpen, FileText, Search } from 'lucide-react';
import { EmptyState } from '../../shared/components/States';
import { Pill } from '../../shared/components/ui';
import type { FinancePolicyCitation } from '../../shared/lib/api';

function toneForCitation(tag: FinancePolicyCitation['relevance_tag']): 'sage' | 'terracotta' | 'sand' {
  if (tag === 'coverage') {
    return 'sage';
  }
  if (tag === 'exclusion') {
    return 'terracotta';
  }
  return 'sand';
}

export function PolicyCitationPanel({
  citations,
  activeCitationId,
  onCitationClick,
}: {
  citations: FinancePolicyCitation[];
  activeCitationId?: string | null;
  onCitationClick: (citationId: string) => void;
}) {
  const [query, setQuery] = useState('');
  const deferredQuery = useDeferredValue(query);

  const filtered = useMemo(() => {
    const normalized = deferredQuery.trim().toLowerCase();
    if (!normalized) {
      return citations;
    }
    return citations.filter((citation) =>
      `${citation.section_title} ${citation.excerpt}`.toLowerCase().includes(normalized),
    );
  }, [citations, deferredQuery]);

  const counts = {
    coverage: citations.filter((citation) => citation.relevance_tag === 'coverage').length,
    exclusion: citations.filter((citation) => citation.relevance_tag === 'exclusion').length,
    limitation: citations.filter((citation) => citation.relevance_tag === 'limitation').length,
  };

  return (
    <section className="glass-panel flex h-full flex-col rounded-[1.25rem] p-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="eyebrow text-primary/70">Policy Citations</p>
          <h3 className="mt-3 font-serif text-[1.5rem] text-on-surface">Coverage references behind the audit</h3>
        </div>
        <div className="rounded-2xl bg-primary-fixed/25 p-3 text-primary">
          <BookOpen className="h-5 w-5" />
        </div>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        <Pill tone="sage">{counts.coverage} coverage</Pill>
        <Pill tone="terracotta">{counts.exclusion} exclusions</Pill>
        <Pill tone="sand">{counts.limitation} limits</Pill>
      </div>

      <label className="relative mt-4 block">
        <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-on-surface/40" />
        <input
          type="text"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search policy language"
          className="input-shell w-full pl-10"
        />
      </label>

      <div className="mt-4 flex-1 space-y-3 overflow-y-auto pr-1">
        {!citations.length ? (
          <EmptyState
            title="No citations yet"
            description="Once the bill audit runs, the most relevant policy passages will appear here."
          />
        ) : filtered.length ? (
          filtered.map((citation) => {
            const isActive = citation.id === activeCitationId;
            return (
              <button
                key={citation.id}
                type="button"
                onClick={() => onCitationClick(citation.id)}
                className={`w-full rounded-[1.1rem] border p-4 text-left transition-all ${
                  isActive
                    ? 'border-primary/50 bg-primary-fixed/18'
                    : 'border-outline-variant/15 bg-white/80 hover:bg-surface-container-lowest/80'
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="font-semibold text-on-surface">{citation.section_title}</p>
                    <p className="mt-1 text-xs uppercase tracking-[0.18em] text-on-surface/40">
                      page {citation.page_number}
                    </p>
                  </div>
                  <Pill tone={toneForCitation(citation.relevance_tag)}>{citation.relevance_tag}</Pill>
                </div>

                <p className="mt-3 text-sm leading-6 text-on-surface/68">{citation.excerpt}</p>

                <div className="mt-3 inline-flex items-center gap-2 text-xs text-primary">
                  <FileText className="h-3.5 w-3.5" />
                  Focus this citation in the bill review
                </div>
              </button>
            );
          })
        ) : (
          <div className="rounded-[1.1rem] bg-surface-container-lowest/60 p-6 text-center text-sm text-on-surface/50">
            No citations matched “{query}”.
          </div>
        )}
      </div>
    </section>
  );
}
