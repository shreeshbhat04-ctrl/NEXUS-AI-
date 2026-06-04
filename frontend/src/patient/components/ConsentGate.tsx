import { useEffect, useRef, useState } from 'react';
import { AnimatePresence, motion } from 'motion/react';
import { AlertTriangle, Loader2, ShieldCheck, X } from 'lucide-react';
import type { FinanceLoanOffer } from '../../shared/lib/api';

const money = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' });

export function ConsentGate({
  isOpen,
  onClose,
  onConfirm,
  selectedOffer,
  gapAmount,
  isSubmitting,
}: {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  selectedOffer: FinanceLoanOffer | null;
  gapAmount: number;
  isSubmitting: boolean;
}) {
  const [checked, setChecked] = useState(false);
  const checkboxRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    if (!isOpen) {
      return;
    }
    setChecked(false);
    checkboxRef.current?.focus();
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen) {
      return;
    }
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && !isSubmitting) {
        onClose();
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [isOpen, isSubmitting, onClose]);

  if (!selectedOffer) {
    return null;
  }

  return (
    <AnimatePresence>
      {isOpen ? (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[120] bg-black/40 backdrop-blur-sm"
            onClick={isSubmitting ? undefined : onClose}
          />

          <div className="fixed inset-0 z-[121] flex items-center justify-center p-4">
            <motion.div
              role="dialog"
              aria-modal="true"
              aria-labelledby="finance-consent-title"
              initial={{ y: 60, opacity: 0, scale: 0.97 }}
              animate={{ y: 0, opacity: 1, scale: 1 }}
              exit={{ y: 60, opacity: 0, scale: 0.97 }}
              transition={{ type: 'spring', damping: 26, stiffness: 240 }}
              className="glass-panel w-full max-w-2xl overflow-hidden rounded-[1.5rem]"
            >
              <div className="flex items-start justify-between gap-4 bg-gradient-to-r from-primary/10 via-primary-fixed/20 to-transparent px-6 py-6">
                <div className="space-y-2">
                  <div className="flex items-center gap-3">
                    <div className="rounded-2xl bg-primary-fixed/35 p-3 text-primary">
                      <ShieldCheck className="h-5 w-5" />
                    </div>
                    <div>
                      <p className="eyebrow text-primary/70">Consent Required</p>
                      <h3 id="finance-consent-title" className="font-serif text-2xl text-on-surface">
                        Review and approve your application
                      </h3>
                    </div>
                  </div>
                  <p className="text-sm text-on-surface/60">
                    We only submit the billing details needed to process this financing request.
                  </p>
                </div>

                <button
                  type="button"
                  onClick={onClose}
                  disabled={isSubmitting}
                  className="rounded-full p-2 text-on-surface/55 transition-colors hover:bg-surface-container-low hover:text-on-surface"
                  aria-label="Close consent dialog"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              <div className="space-y-5 px-6 py-6">
                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="rounded-[1.1rem] bg-surface-container-lowest/70 p-4">
                    <p className="eyebrow text-on-surface/45">Provider</p>
                    <p className="mt-2 text-lg font-semibold text-on-surface">{selectedOffer.provider_name}</p>
                  </div>
                  <div className="rounded-[1.1rem] bg-surface-container-lowest/70 p-4">
                    <p className="eyebrow text-on-surface/45">Loan amount</p>
                    <p className="mt-2 text-lg font-semibold text-on-surface">{money.format(gapAmount)}</p>
                  </div>
                  <div className="rounded-[1.1rem] bg-surface-container-lowest/70 p-4">
                    <p className="eyebrow text-on-surface/45">APR</p>
                    <p className="mt-2 text-lg font-semibold text-on-surface">{selectedOffer.apr.toFixed(2)}%</p>
                  </div>
                  <div className="rounded-[1.1rem] bg-surface-container-lowest/70 p-4">
                    <p className="eyebrow text-on-surface/45">EMI</p>
                    <p className="mt-2 text-lg font-semibold text-on-surface">{money.format(Number(selectedOffer.emi))}</p>
                  </div>
                  <div className="rounded-[1.1rem] bg-surface-container-lowest/70 p-4">
                    <p className="eyebrow text-on-surface/45">Tenure</p>
                    <p className="mt-2 text-lg font-semibold text-on-surface">{selectedOffer.tenure_months} months</p>
                  </div>
                  <div className="rounded-[1.1rem] bg-surface-container-lowest/70 p-4">
                    <p className="eyebrow text-on-surface/45">Total payable</p>
                    <p className="mt-2 text-lg font-semibold text-on-surface">{money.format(Number(selectedOffer.total_payable))}</p>
                  </div>
                </div>

                <div className="rounded-[1.15rem] bg-tertiary-container/18 p-4 text-sm leading-7 text-on-surface/72">
                  <div className="flex items-start gap-3">
                    <AlertTriangle className="mt-1 h-4 w-4 shrink-0 text-tertiary" />
                    <p>
                      By proceeding, you authorize Cure-Quest to share the minimum necessary billing details with
                      {` ${selectedOffer.provider_name} `}solely to process this healthcare financing request. No clinical notes
                      or full medical records are included in this submission flow.
                    </p>
                  </div>
                </div>

                <label className="flex items-start gap-3 rounded-[1.1rem] bg-white/80 p-4">
                  <input
                    ref={checkboxRef}
                    type="checkbox"
                    checked={checked}
                    onChange={(event) => setChecked(event.target.checked)}
                    className="mt-1 h-4 w-4 rounded border-outline-variant accent-primary"
                  />
                  <span className="text-sm leading-6 text-on-surface/78">
                    I understand the billing disclosure above and agree to continue with this loan submission.
                  </span>
                </label>
              </div>

              <div className="flex flex-col gap-3 border-t border-outline-variant/15 px-6 py-5 sm:flex-row">
                <button
                  type="button"
                  onClick={onClose}
                  disabled={isSubmitting}
                  className="river-stone-btn flex-1 border border-outline-variant/35 bg-transparent px-5 py-3 text-on-surface/70 hover:bg-surface-container-low"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={onConfirm}
                  disabled={!checked || isSubmitting}
                  className="river-stone-btn flex-1 bg-gradient-to-br from-primary to-primary-container px-5 py-3 font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {isSubmitting ? (
                    <span className="inline-flex items-center gap-2">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Submitting
                    </span>
                  ) : (
                    'Confirm and Apply'
                  )}
                </button>
              </div>
            </motion.div>
          </div>
        </>
      ) : null}
    </AnimatePresence>
  );
}
