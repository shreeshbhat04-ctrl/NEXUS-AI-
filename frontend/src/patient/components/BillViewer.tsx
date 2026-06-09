import type { ReactNode } from 'react';
import { AlertTriangle, CheckCircle2, ExternalLink, FileText, ReceiptText, SearchX } from 'lucide-react';
import { motion } from 'motion/react';
import { Pill } from '../../shared/components/ui';
import type { FinanceAuditFlag, FinanceBillItem } from '../../shared/lib/api';

const money = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' });

function toneForFlag(type: FinanceAuditFlag['type']): 'terracotta' | 'sand' | 'sage' {
  if (type === 'duplicate' || type === 'math_error') {
    return 'terracotta';
  }
  if (type === 'unknown_code' || type === 'pricing_outlier') {
    return 'sand';
  }
  return 'sage';
}

function iconForFlag(type: FinanceAuditFlag['type']) {
  if (type === 'verified') {
    return <CheckCircle2 className="h-4 w-4" />;
  }
  if (type === 'unknown_code') {
    return <SearchX className="h-4 w-4" />;
  }
  return <AlertTriangle className="h-4 w-4" />;
}

export function BillViewer({
  fileName,
  pdfUrl,
  items,
  flags,
  activeCitationId,
  pdfViewer,
}: {
  fileName?: string | null;
  pdfUrl?: string | null;
  items: FinanceBillItem[];
  flags: FinanceAuditFlag[];
  activeCitationId?: string | null;
  pdfViewer?: ReactNode;
}) {
  const flagsByIndex = new Map<number, FinanceAuditFlag[]>();
  for (const flag of flags) {
    const existing = flagsByIndex.get(flag.item_index) ?? [];
    existing.push(flag);
    flagsByIndex.set(flag.item_index, existing);
  }

  const counts = {
    terracotta: flags.filter((flag) => toneForFlag(flag.type) === 'terracotta').length,
    sand: flags.filter((flag) => toneForFlag(flag.type) === 'sand').length,
    sage: flags.filter((flag) => toneForFlag(flag.type) === 'sage').length,
  };

  return (
    <section className="glass-panel overflow-hidden rounded-[1.25rem]">
      <div className="flex flex-wrap items-start justify-between gap-4 border-b border-outline-variant/20 bg-white/75 px-6 py-5">
        <div className="space-y-2">
          <div className="flex items-center gap-3">
            <div className="rounded-2xl bg-primary-fixed/30 p-3 text-primary">
              <FileText className="h-5 w-5" />
            </div>
            <div>
              <p className="eyebrow text-primary/70">Bill Review</p>
              <h3 className="font-serif text-2xl text-on-surface">Itemized charges and audit flags</h3>
            </div>
          </div>
          <p className="text-sm text-on-surface/55">
            {fileName ?? 'Uploaded bill'} with {items.length} line items.
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          <Pill tone="terracotta">{counts.terracotta} flagged</Pill>
          <Pill tone="sand">{counts.sand} needs review</Pill>
          <Pill tone="sage">{counts.sage} verified</Pill>
          {pdfUrl ? (
            <a
              className="inline-flex items-center gap-2 rounded-full bg-surface-container-low px-4 py-2 text-xs font-medium text-primary transition-colors hover:bg-primary-fixed/30"
              href={pdfUrl}
              target="_blank"
              rel="noreferrer"
            >
              Open PDF
              <ExternalLink className="h-3.5 w-3.5" />
            </a>
          ) : null}
        </div>
      </div>

      {/* Embedded PDF Viewer */}
      {pdfViewer ? (
        <div className="border-b border-outline-variant/20 p-4">
          {pdfViewer}
        </div>
      ) : null}

      <div className="grid gap-0 xl:grid-cols-[1.15fr_0.85fr]">
        <div className="border-b border-outline-variant/20 xl:border-b-0 xl:border-r">
          <div className="grid grid-cols-[minmax(0,1.8fr)_0.75fr_0.7fr_0.8fr] gap-3 px-6 py-3 text-[0.7rem] font-semibold uppercase tracking-[0.18em] text-on-surface/45">
            <span>Description</span>
            <span>Code</span>
            <span>Qty</span>
            <span>Total</span>
          </div>

          <div className="space-y-2 px-4 py-4">
            {items.map((item, index) => {
              const linkedFlags = flagsByIndex.get(index) ?? [];
              const hasActiveCitation = linkedFlags.some((flag) => flag.policy_citation_ids.includes(activeCitationId ?? ''));
              return (
                <motion.div
                  key={`${item.code}-${index}`}
                  layout
                  className={`rounded-[1.1rem] border px-4 py-4 transition-colors ${
                    hasActiveCitation
                      ? 'border-primary/50 bg-primary-fixed/20'
                      : 'border-outline-variant/15 bg-surface-container-lowest/55'
                  }`}
                >
                  <div className="grid grid-cols-[minmax(0,1.8fr)_0.75fr_0.7fr_0.8fr] gap-3">
                    <div>
                      <p className="font-semibold text-on-surface">{item.description}</p>
                      <p className="mt-1 text-xs text-on-surface/50">{item.category}</p>
                    </div>
                    <p className="text-sm text-on-surface/70">{item.code}</p>
                    <p className="text-sm text-on-surface/70">{item.quantity}</p>
                    <p className="text-sm font-semibold text-on-surface">{money.format(Number(item.line_total))}</p>
                  </div>

                  {linkedFlags.length ? (
                    <div className="mt-3 flex flex-wrap gap-2">
                      {linkedFlags.map((flag) => (
                        <span
                          key={flag.id}
                          className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-medium ${
                            toneForFlag(flag.type) === 'terracotta'
                              ? 'bg-secondary-container/35 text-secondary'
                              : toneForFlag(flag.type) === 'sand'
                                ? 'bg-tertiary-container/28 text-tertiary'
                                : 'bg-primary-fixed/40 text-primary'
                          }`}
                        >
                          {iconForFlag(flag.type)}
                          {flag.reason}
                        </span>
                      ))}
                    </div>
                  ) : null}
                </motion.div>
              );
            })}
          </div>
        </div>

        <div className="space-y-3 px-4 py-4">
          <div className="rounded-[1.1rem] bg-surface-container-lowest/55 p-4">
            <p className="eyebrow text-on-surface/50">Audit Focus</p>
            <h4 className="mt-3 font-serif text-xl text-on-surface">Why these charges were flagged</h4>
          </div>

          {flags.map((flag) => (
            <div
              key={flag.id}
              className={`rounded-[1.1rem] border p-4 ${
                flag.policy_citation_ids.includes(activeCitationId ?? '')
                  ? 'border-primary/50 bg-primary-fixed/15'
                  : 'border-outline-variant/15 bg-white/80'
              }`}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="space-y-2">
                  <Pill tone={toneForFlag(flag.type)}>{flag.type.replace('_', ' ')}</Pill>
                  <p className="font-semibold text-on-surface">{flag.line_item_description}</p>
                  <p className="text-sm leading-6 text-on-surface/65">{flag.reason}</p>
                </div>
                <div className="rounded-2xl bg-surface-container-low p-3 text-on-surface/70">
                  <ReceiptText className="h-4 w-4" />
                </div>
              </div>

              <div className="mt-4 grid gap-3 sm:grid-cols-2">
                <div className="rounded-xl bg-surface-container-lowest/70 p-3">
                  <p className="eyebrow text-on-surface/45">Billed</p>
                  <p className="mt-2 text-lg font-semibold text-on-surface">{money.format(Number(flag.billed_amount))}</p>
                </div>
                <div className="rounded-xl bg-surface-container-lowest/70 p-3">
                  <p className="eyebrow text-on-surface/45">Verified</p>
                  <p className="mt-2 text-lg font-semibold text-on-surface">
                    {flag.verified_amount ? money.format(Number(flag.verified_amount)) : 'Pending'}
                  </p>
                </div>
              </div>

              <p className="mt-3 text-sm leading-6 text-on-surface/58">{flag.suggested_action}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
