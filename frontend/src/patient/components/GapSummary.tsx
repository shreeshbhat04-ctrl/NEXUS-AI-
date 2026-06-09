import { DollarSign, ShieldCheck, Wallet } from 'lucide-react';
import { motion } from 'motion/react';
import { Pill } from '../../shared/components/ui';
import { CitationMarker } from './CitationMarker';
import type { FinanceGapResult, FinancePolicyCitation } from '../../shared/lib/api';

const money = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' });

function percentage(part: number, total: number) {
  if (!total) {
    return 0;
  }
  return Math.round((part / total) * 100);
}

export function GapSummary({
  gapResult,
  citations,
  onCitationClick,
}: {
  gapResult: FinanceGapResult;
  citations: FinancePolicyCitation[];
  onCitationClick?: (citationId: string) => void;
}) {
  const totalBilled = Number(gapResult.total_billed);
  const coverage = Number(gapResult.insurance_coverage);
  const responsibility = Number(gapResult.patient_responsibility);
  const breakdown = gapResult.breakdown;
  const oopProgress = percentage(Number(breakdown.out_of_pocket_spent), Number(breakdown.out_of_pocket_max));

  return (
    <section className="glass-panel rounded-[1.25rem] p-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="eyebrow text-primary/70">Financial Gap</p>
          <h3 className="mt-3 font-serif text-[1.8rem] text-on-surface">Coverage versus your out-of-pocket balance</h3>
        </div>
        <Pill tone={responsibility > 0 ? 'terracotta' : 'sage'}>
          {responsibility > 0 ? 'Financing may help' : 'Fully covered'}
        </Pill>
      </div>

      <div className="mt-6 grid gap-4 md:grid-cols-3">
        <div className="rounded-[1.25rem] bg-[#e8f0fe] px-5 py-5">
          <p className="eyebrow text-primary/75">Total billed</p>
          <p className="mt-3 text-[2rem] font-bold text-on-surface">{money.format(totalBilled)}</p>
        </div>
        <div className="rounded-[1.25rem] bg-[#e6f4ea] px-5 py-5">
          <p className="eyebrow text-[#34a853]">Insurance covered</p>
          <p className="mt-3 text-[2rem] font-bold text-on-surface">{money.format(coverage)}</p>
        </div>
        <div className="rounded-[1.25rem] bg-[#fce8e6] px-5 py-5">
          <p className="eyebrow text-secondary/85">Patient balance</p>
          <p className="mt-3 text-[2rem] font-bold text-on-surface">{money.format(responsibility)}</p>
        </div>
      </div>

      <div className="mt-6 rounded-[1.25rem] bg-surface-container-lowest/60 p-5">
        <div className="flex items-center justify-between gap-4">
          <div>
            <p className="eyebrow text-on-surface/50">Share of bill</p>
            <p className="mt-2 font-serif text-xl text-on-surface">
              {percentage(responsibility, totalBilled)}% remains with the patient
            </p>
          </div>
          <div className="flex gap-3 text-sm text-on-surface/55">
            <span className="inline-flex items-center gap-2">
              <span className="h-3 w-3 rounded-full bg-[#34a853]" />
              Covered
            </span>
            <span className="inline-flex items-center gap-2">
              <span className="h-3 w-3 rounded-full bg-[#ea4335]" />
              Your share
            </span>
          </div>
        </div>

        <div className="mt-5 overflow-hidden rounded-full bg-surface-container-low">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${percentage(coverage, totalBilled)}%` }}
            transition={{ duration: 0.8 }}
            className="h-4 rounded-full bg-[#34a853]"
          />
        </div>
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${percentage(responsibility, totalBilled)}%` }}
          transition={{ duration: 0.8, delay: 0.12 }}
          className="-mt-4 h-4 rounded-full bg-[#ea4335]"
        />
      </div>

      <div className="mt-6 grid gap-3 md:grid-cols-2">
        <div className="rounded-[1.1rem] bg-white/80 p-4">
          <div className="flex items-center gap-3">
            <ShieldCheck className="h-4 w-4 text-primary" />
            <p className="eyebrow text-on-surface/45">Deductible remaining</p>
          </div>
          <p className="mt-3 text-xl font-semibold text-on-surface">{money.format(Number(breakdown.deductible_remaining))}</p>
        </div>
        <div className="rounded-[1.1rem] bg-white/80 p-4">
          <div className="flex items-center gap-3">
            <Wallet className="h-4 w-4 text-primary" />
            <p className="eyebrow text-on-surface/45">Coinsurance</p>
          </div>
          <p className="mt-3 text-xl font-semibold text-on-surface">
            {breakdown.coinsurance_percent}% / {money.format(Number(breakdown.coinsurance_amount))}
          </p>
        </div>
        <div className="rounded-[1.1rem] bg-white/80 p-4">
          <div className="flex items-center gap-3">
            <DollarSign className="h-4 w-4 text-primary" />
            <p className="eyebrow text-on-surface/45">Copay</p>
          </div>
          <p className="mt-3 text-xl font-semibold text-on-surface">{money.format(Number(breakdown.copay))}</p>
        </div>
        <div className="rounded-[1.1rem] bg-white/80 p-4">
          <p className="eyebrow text-on-surface/45">Out-of-pocket progress</p>
          <p className="mt-3 text-xl font-semibold text-on-surface">
            {money.format(Number(breakdown.out_of_pocket_spent))} / {money.format(Number(breakdown.out_of_pocket_max))}
          </p>
          <div className="mt-3 h-2 overflow-hidden rounded-full bg-surface-container-low">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${Math.max(0, Math.min(100, oopProgress))}%` }}
              transition={{ duration: 0.8 }}
              className="h-full rounded-full bg-gradient-to-r from-primary to-[#34a853]"
            />
          </div>
        </div>
      </div>

      {citations.length ? (
        <div className="mt-6 space-y-3 rounded-[1.1rem] bg-primary-fixed/12 p-4">
          <p className="eyebrow text-primary/70">Coverage references</p>
          {citations.slice(0, 2).map((citation, index) => (
            <div
              key={citation.id}
              className="block w-full rounded-xl bg-white/70 px-4 py-3 text-left text-sm leading-6 text-on-surface/72 transition-colors hover:bg-white"
            >
              <div className="flex items-center gap-2">
                <span className="font-semibold text-primary">{citation.section_title}</span>
                <CitationMarker
                  index={index + 1}
                  citation={citation}
                  isActive={false}
                  onActivate={onCitationClick ?? (() => {})}
                />
              </div>
              <span className="block mt-1">{citation.excerpt}</span>
            </div>
          ))}
        </div>
      ) : null}
    </section>
  );
}
