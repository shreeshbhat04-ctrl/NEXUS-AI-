import { Award, BadgePercent, CalendarRange, CheckCircle2, ShieldCheck, WalletCards } from 'lucide-react';
import { motion } from 'motion/react';
import { EmptyState } from '../../shared/components/States';
import { Pill } from '../../shared/components/ui';
import type { FinanceLoanOffer } from '../../shared/lib/api';

const money = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' });

function aprTone(apr: number) {
  if (apr <= 6) {
    return 'text-primary';
  }
  if (apr <= 12) {
    return 'text-tertiary';
  }
  return 'text-secondary';
}

export function LoanComparison({
  offers,
  selectedOfferId,
  onSelectOffer,
}: {
  offers: FinanceLoanOffer[];
  selectedOfferId: string | null;
  onSelectOffer: (offerId: string) => void;
}) {
  if (!offers.length) {
    return (
      <EmptyState
        title="No financing options yet"
        description="Upload and audit a bill first, then the ranked loan options will appear here."
      />
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-end justify-between gap-4">
        <div>
          <p className="eyebrow text-primary/70">Loan Options</p>
          <h3 className="mt-3 font-serif text-[1.8rem] text-on-surface">Financing tailored to the uncovered balance</h3>
        </div>
        <Pill tone="sage">{offers.length} offers ranked</Pill>
      </div>

      <div className="grid gap-4">
        {offers.map((offer, index) => {
          const isSelected = offer.id === selectedOfferId;
          return (
            <motion.button
              key={offer.id}
              type="button"
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.06 }}
              whileTap={{ scale: 0.99 }}
              onClick={() => onSelectOffer(offer.id)}
              className={`glass-panel relative overflow-hidden rounded-[1.25rem] p-5 text-left transition-all ${
                isSelected ? 'ring-2 ring-primary/60' : 'hover:ring-1 hover:ring-primary/25'
              }`}
            >
              <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-primary via-[#7bc9ff] to-[#34a853]" />

              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-lg font-semibold text-on-surface">{offer.provider_name}</p>
                  <p className="mt-1 text-sm text-on-surface/55">
                    Reliability score {(offer.provider_reliability_score * 100).toFixed(0)}%
                  </p>
                </div>

                <div className="flex flex-wrap gap-2">
                  {offer.is_top_pick ? (
                    <Pill tone="sage">
                      <span className="inline-flex items-center gap-1">
                        <Award className="h-3.5 w-3.5" />
                        Best fit
                      </span>
                    </Pill>
                  ) : null}
                  {isSelected ? (
                    <Pill tone="terracotta">
                      <span className="inline-flex items-center gap-1">
                        <CheckCircle2 className="h-3.5 w-3.5" />
                        Selected
                      </span>
                    </Pill>
                  ) : null}
                </div>
              </div>

              <div className="mt-5 grid gap-3 sm:grid-cols-2">
                <div className="rounded-xl bg-surface-container-lowest/70 p-4">
                  <p className="eyebrow text-on-surface/45">APR</p>
                  <p className={`mt-2 text-xl font-semibold ${aprTone(offer.apr)}`}>{offer.apr.toFixed(2)}%</p>
                  <div className="mt-2 flex items-center gap-2 text-xs text-on-surface/50">
                    <BadgePercent className="h-3.5 w-3.5" />
                    Interest rate
                  </div>
                </div>

                <div className="rounded-xl bg-surface-container-lowest/70 p-4">
                  <p className="eyebrow text-on-surface/45">Monthly EMI</p>
                  <p className="mt-2 text-xl font-semibold text-on-surface">{money.format(Number(offer.emi))}</p>
                  <div className="mt-2 flex items-center gap-2 text-xs text-on-surface/50">
                    <WalletCards className="h-3.5 w-3.5" />
                    Monthly installment
                  </div>
                </div>

                <div className="rounded-xl bg-surface-container-lowest/70 p-4">
                  <p className="eyebrow text-on-surface/45">Tenure</p>
                  <p className="mt-2 text-xl font-semibold text-on-surface">{offer.tenure_months} months</p>
                  <div className="mt-2 flex items-center gap-2 text-xs text-on-surface/50">
                    <CalendarRange className="h-3.5 w-3.5" />
                    Repayment window
                  </div>
                </div>

                <div className="rounded-xl bg-surface-container-lowest/70 p-4">
                  <p className="eyebrow text-on-surface/45">Total payable</p>
                  <p className="mt-2 text-xl font-semibold text-on-surface">{money.format(Number(offer.total_payable))}</p>
                  <div className="mt-2 flex items-center gap-2 text-xs text-on-surface/50">
                    <ShieldCheck className="h-3.5 w-3.5" />
                    Approval {(offer.approval_probability * 100).toFixed(0)}%
                  </div>
                </div>
              </div>

              <div className="mt-4 h-2 overflow-hidden rounded-full bg-surface-container-low">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-primary to-[#34a853]"
                  style={{ width: `${Math.max(12, Math.min(100, offer.approval_probability * 100))}%` }}
                />
              </div>
            </motion.button>
          );
        })}
      </div>
    </div>
  );
}
