import { startTransition, useMemo, useRef, useState } from 'react';
import { motion } from 'motion/react';
import {
  CheckCircle2,
  FileSearch,
  Landmark,
  Loader2,
  Receipt,
  RefreshCw,
  ShieldCheck,
  Upload,
} from 'lucide-react';
import type { WorkspacePayload } from '../../shared/lib/api';
import { EmptyState, ErrorState, LoadingState } from '../../shared/components/States';
import { Pill, SectionShell } from '../../shared/components/ui';
import { BillViewer } from '../components/BillViewer';
import { ConsentGate } from '../components/ConsentGate';
import { GapSummary } from '../components/GapSummary';
import { LoanComparison } from '../components/LoanComparison';
import { PolicyCitationPanel } from '../components/PolicyCitationPanel';
import { useFinancialWorkflow } from '../hooks/useFinancialWorkflow';

const money = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' });

const STEPS = [
  { id: 'uploading', label: 'Upload', icon: Upload },
  { id: 'parsing', label: 'Parse', icon: FileSearch },
  { id: 'auditing', label: 'Audit', icon: Receipt },
  { id: 'gap_calculating', label: 'Gap', icon: ShieldCheck },
  { id: 'loan_discovery', label: 'Loan Match', icon: Landmark },
  { id: 'awaiting_consent', label: 'Consent', icon: ShieldCheck },
  { id: 'submitted', label: 'Submitted', icon: CheckCircle2 },
] as const;

type StepId = (typeof STEPS)[number]['id'];

export function FinancialAdvocateScreen({
  patientId,
  workspace,
  loading,
  error,
  onRefresh,
}: {
  patientId: number;
  workspace: WorkspacePayload | null;
  loading: boolean;
  error: string | null;
  onRefresh: () => void;
}) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [showConsent, setShowConsent] = useState(false);
  const [isDragActive, setIsDragActive] = useState(false);
  const [activeCitationId, setActiveCitationId] = useState<string | null>(null);

  const workflow = useFinancialWorkflow(patientId);

  const activeStepIndex = useMemo(() => {
    const index = STEPS.findIndex((step) => step.id === workflow.currentStep);
    return index === -1 ? -1 : index;
  }, [workflow.currentStep]);

  if (loading && !workspace) return <LoadingState />;
  if (error && !workspace) return <ErrorState message={error} onRetry={onRefresh} />;
  if (!workspace) return <ErrorState message="No workspace loaded." onRetry={onRefresh} />;

  const firstName = workspace.patient.full_name.split(' ')[0] ?? 'there';
  const auditResult = workflow.auditResult;
  const gapResult = workflow.gapResult;

  const handleFile = async (file?: File | null) => {
    if (!file) {
      return;
    }
    setActiveCitationId(null);
    await workflow.uploadBill(file);
  };

  const handleCitationClick = (citationId: string) => {
    startTransition(() => setActiveCitationId(citationId));
  };

  const openPicker = () => inputRef.current?.click();

  return (
    <motion.div initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -18 }} className="space-y-8 pb-12">
      <SectionShell
        eyebrow="Financial Advocate"
        title={
          <>
            Bills decoded for <span className="text-primary italic font-serif">{firstName}</span>, with coverage and financing in one flow.
          </>
        }
        description={workflow.statusMessage}
      >
        <div className="flex flex-wrap gap-3">
          <Pill tone="sage">{workflow.loanOffers.length} offers ranked</Pill>
          <Pill tone="sand">{workflow.policyCitations.length} policy citations</Pill>
          {gapResult ? <Pill tone="terracotta">{money.format(Number(gapResult.patient_responsibility))} patient balance</Pill> : null}
        </div>
      </SectionShell>

      <section className="glass-panel rounded-[1.25rem] p-5">
        <div className="flex flex-wrap items-center gap-3">
          {STEPS.map((step, index) => {
            const Icon = step.icon;
            const isActive = step.id === workflow.currentStep;
            const isCompleted = activeStepIndex > index || workflow.currentStep === 'submitted';
            return (
              <div key={step.id} className="flex items-center gap-3">
                <div
                  className={`inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium ${
                    isActive
                      ? 'bg-secondary-container/35 text-secondary'
                      : isCompleted
                        ? 'bg-primary-fixed/40 text-primary'
                        : 'bg-surface-container-low text-on-surface/45'
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  {step.label}
                  {isActive && workflow.isProcessing ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
                </div>
                {index < STEPS.length - 1 ? <div className="hidden h-px w-6 bg-outline-variant/35 sm:block" /> : null}
              </div>
            );
          })}
        </div>
      </section>

      <div className="grid gap-6 xl:grid-cols-[1.25fr_0.75fr]">
        <div className="space-y-6">
          <section
            className={`glass-panel rounded-[1.25rem] border-2 border-dashed p-8 transition-colors ${
              isDragActive ? 'border-primary/60 bg-primary-fixed/10' : 'border-outline-variant/25'
            }`}
            onDragOver={(event) => {
              event.preventDefault();
              setIsDragActive(true);
            }}
            onDragLeave={() => setIsDragActive(false)}
            onDrop={(event) => {
              event.preventDefault();
              setIsDragActive(false);
              void handleFile(event.dataTransfer.files?.[0]);
            }}
          >
            <input
              ref={inputRef}
              type="file"
              accept="application/pdf,.pdf"
              className="hidden"
              onChange={(event) => void handleFile(event.target.files?.[0])}
            />

            <div className="flex flex-col items-center text-center">
              <div className="rounded-[1.5rem] bg-primary-fixed/30 p-5 text-primary">
                <Upload className="h-8 w-8" />
              </div>
              <p className="mt-5 font-serif text-[1.7rem] text-on-surface">Drop a hospital bill PDF here</p>
              <p className="mt-3 max-w-2xl text-sm leading-7 text-on-surface/60">
                We audit duplicate charges, estimate coverage, attach policy citations, and rank financing offers on the same screen.
              </p>

              <div className="mt-6 flex flex-wrap justify-center gap-3">
                <button
                  type="button"
                  onClick={openPicker}
                  className="river-stone-btn bg-gradient-to-br from-primary to-primary-container px-5 py-3 font-semibold text-white"
                >
                  Choose PDF
                </button>
                {workflow.billId ? (
                  <button
                    type="button"
                    onClick={workflow.reset}
                    className="river-stone-btn border border-outline-variant/35 bg-transparent px-5 py-3 text-on-surface/70 hover:bg-surface-container-low"
                  >
                    Reset workflow
                  </button>
                ) : null}
              </div>

              {workflow.isUploading ? (
                <div className="mt-6 w-full max-w-md">
                  <div className="h-2 overflow-hidden rounded-full bg-surface-container-low">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-primary to-[#34a853]"
                      style={{ width: `${workflow.uploadProgress}%` }}
                    />
                  </div>
                  <p className="mt-3 text-xs uppercase tracking-[0.18em] text-on-surface/40">Processing upload</p>
                </div>
              ) : null}
            </div>
          </section>

          {workflow.error ? (
            <div className="rounded-[1.25rem] bg-secondary-container/25 p-4 text-sm text-secondary">
              <div className="flex items-start justify-between gap-4">
                <p>{workflow.error}</p>
                <button
                  type="button"
                  onClick={() => void workflow.retryCurrentStep()}
                  className="inline-flex items-center gap-2 rounded-full bg-white/70 px-4 py-2 text-xs font-semibold text-secondary"
                >
                  <RefreshCw className="h-3.5 w-3.5" />
                  Retry
                </button>
              </div>
            </div>
          ) : null}

          {auditResult ? (
            <>
              <div className="grid gap-4 md:grid-cols-3">
                <div className="rounded-[1.25rem] bg-[#e8f0fe] px-5 py-5">
                  <p className="eyebrow text-primary/75">Total billed</p>
                  <p className="mt-3 text-[1.9rem] font-bold text-on-surface">{money.format(Number(auditResult.total_billed))}</p>
                </div>
                <div className="rounded-[1.25rem] bg-[#fce8e6] px-5 py-5">
                  <p className="eyebrow text-secondary/85">Flagged value</p>
                  <p className="mt-3 text-[1.9rem] font-bold text-on-surface">{money.format(Number(auditResult.total_flagged))}</p>
                </div>
                <div className="rounded-[1.25rem] bg-[#e6f4ea] px-5 py-5">
                  <p className="eyebrow text-[#34a853]">Verified value</p>
                  <p className="mt-3 text-[1.9rem] font-bold text-on-surface">{money.format(Number(auditResult.total_verified))}</p>
                </div>
              </div>

              <BillViewer
                fileName={workflow.snapshot?.pdf_filename ?? null}
                pdfUrl={workflow.pdfUrl}
                items={auditResult.items}
                flags={auditResult.flags}
                activeCitationId={activeCitationId}
              />
            </>
          ) : (
            <EmptyState
              title="No bill uploaded yet"
              description="Once you upload a PDF, the itemized bill review and flagged charge analysis will appear here."
            />
          )}

          {gapResult ? (
            <GapSummary gapResult={gapResult} citations={workflow.policyCitations} onCitationClick={handleCitationClick} />
          ) : null}
        </div>

        <div className="space-y-6">
          <PolicyCitationPanel
            citations={workflow.policyCitations}
            activeCitationId={activeCitationId}
            onCitationClick={handleCitationClick}
          />

          <section className="glass-panel rounded-[1.25rem] p-5">
            <LoanComparison
              offers={workflow.loanOffers}
              selectedOfferId={workflow.selectedOfferId}
              onSelectOffer={workflow.selectOffer}
            />

            {workflow.selectedOffer && workflow.currentStep !== 'submitted' ? (
              <button
                type="button"
                onClick={() => setShowConsent(true)}
                className="river-stone-btn mt-5 w-full bg-gradient-to-br from-primary to-primary-container px-5 py-3 font-semibold text-white"
              >
                Apply for selected financing
              </button>
            ) : null}

            {workflow.applicationId ? (
              <div className="mt-5 rounded-[1.15rem] bg-primary-fixed/18 p-4">
                <div className="flex items-start gap-3">
                  <div className="rounded-2xl bg-white/80 p-3 text-primary">
                    <CheckCircle2 className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="font-semibold text-on-surface">Application submitted</p>
                    <p className="mt-1 text-sm leading-6 text-on-surface/65">
                      Reference ID: {workflow.applicationId}. The patient-side financing handoff is complete.
                    </p>
                  </div>
                </div>
              </div>
            ) : null}
          </section>
        </div>
      </div>

      <ConsentGate
        isOpen={showConsent}
        onClose={() => setShowConsent(false)}
        onConfirm={async () => {
          const submitted = await workflow.submitApplication();
          if (submitted) {
            setShowConsent(false);
          }
        }}
        selectedOffer={workflow.selectedOffer}
        gapAmount={Number(gapResult?.patient_responsibility ?? 0)}
        isSubmitting={workflow.isSubmitting}
      />
    </motion.div>
  );
}
