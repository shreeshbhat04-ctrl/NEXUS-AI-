import { motion } from 'motion/react';
import { Sparkles, ShieldCheck, Info, CalendarDays, Phone, Brain } from 'lucide-react';
import type { WorkspacePayload } from '../lib/api';
import { ErrorState, LoadingState } from '../components/States';
import { SectionShell, SoftCard, Pill } from '../components/ui';

export function AboutScreen({
  workspace,
  loading,
  error,
  onRefresh,
}: {
  workspace: WorkspacePayload | null;
  loading: boolean;
  error: string | null;
  onRefresh: () => void;
}) {
  if (loading && !workspace) return <LoadingState />;
  if (error && !workspace) return <ErrorState message={error} onRetry={onRefresh} />;
  if (!workspace) return <ErrorState message="No workspace loaded." onRetry={onRefresh} />;

  const { patient, conditions, manifest } = workspace;

  return (
    <motion.div initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -18 }} className="space-y-8">
      <SectionShell
        eyebrow="About"
        title={
          <>
            Under the hood of <span className="text-primary italic">nexus_ai</span>.
          </>
        }
        description="A look at the AI model choreography and system context powering your experience."
      />

      <div className="grid gap-6 xl:grid-cols-[1fr]">
        <SoftCard>
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="eyebrow text-primary/75">Agent fabric</p>
              <h2 className="mt-3 font-serif text-[1.7rem] leading-tight">Model choreography</h2>
            </div>
            <div className="rounded-full bg-primary-fixed/45 p-3 text-primary">
              <Sparkles className="h-5 w-5" />
            </div>
          </div>
          <div className="mt-6 space-y-4">
            {Object.entries(manifest.agent_manifest).map(([agentKey, agent]) => (
              <div key={agentKey} className="soft-panel">
                <div className="flex items-center justify-between gap-3">
                  <p className="text-[1rem] font-medium capitalize">{agentKey.replaceAll('_', ' ')}</p>
                  <Pill tone="sage">{agent.primary_model}</Pill>
                </div>
                <p className="mt-2 text-[0.92rem] leading-7 text-on-surface/58">{agent.reason}</p>
              </div>
            ))}
          </div>
        </SoftCard>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <SoftCard className="bg-surface-container-low">
          <div className="flex items-center gap-3 text-primary">
            <ShieldCheck className="h-5 w-5" />
            <h3 className="font-serif text-[1.35rem]">Chronic context</h3>
          </div>
          <div className="mt-5 flex flex-wrap gap-3">
            {conditions.map((condition) => (
              <span key={condition.id}>
                <Pill tone="sand">{condition.name}</Pill>
              </span>
            ))}
          </div>
          <p className="mt-4 text-[0.92rem] leading-7 text-on-surface/60">This context is automatically injected into relevant LLM prompts to ensure safe and personalized interactions.</p>
        </SoftCard>

        <SoftCard className="bg-surface-container-low">
          <div className="flex items-center gap-3 text-primary">
            <Info className="h-5 w-5" />
            <h3 className="font-serif text-[1.35rem]">Response language</h3>
          </div>
          <p className="mt-3 text-[1.05rem]">{patient.preferred_language.toUpperCase()}</p>
          <p className="mt-2 text-[0.92rem] leading-7 text-on-surface/60">The communication agent keeps the tone soft while using Gemini 3.1 Flash where needed.</p>
        </SoftCard>
      </div>

      <SoftCard className="bg-surface-container-low">
        <div className="flex items-center gap-3 text-tertiary">
          <Brain className="h-5 w-5" />
          <h3 className="font-serif text-[1.35rem]">AlloyDB & Gemini 3.1 Flash</h3>
        </div>
        <p className="mt-4 text-[0.92rem] leading-7 text-on-surface/60">
          The platform uses AlloyDB for reliable data grounding and Gemini 3.1 Flash for fast, advanced medical reasoning, generating clinical insights and orchestrating workflows.
        </p>
      </SoftCard>

      <div className="grid gap-6 md:grid-cols-3">
        <SoftCard className="bg-surface-container-low">
          <div className="flex items-center gap-3 text-primary">
            <CalendarDays className="h-5 w-5" />
            <h3 className="font-serif text-xl">Calendar-ready</h3>
          </div>
          <p className="mt-3 text-sm leading-7 text-on-surface/60">Follow-ups feed the same Google Calendar connection already used by the escalation flow.</p>
        </SoftCard>
        <SoftCard className="bg-surface-container-low">
          <h3 className="font-serif text-xl text-primary">Condition-aware</h3>
          <p className="mt-3 text-sm leading-7 text-on-surface/60">The diet and pharmacy suggestions stay grounded in the patient’s chronic condition memory before they turn into doctor-facing handoffs.</p>
        </SoftCard>
        <SoftCard className="bg-surface-container-low">
          <h3 className="font-serif text-xl text-primary">MCP-compatible</h3>
          <p className="mt-3 text-sm leading-7 text-on-surface/60">Using backend routes that can stay compatible when more of the logic moves behind MCP tools later.</p>
        </SoftCard>
      </div>

      <div className="grid gap-6 xl:grid-cols-1">
        <SoftCard className="bg-tertiary-container/18">
          <p className="mb-2 font-serif text-[1.1rem] text-tertiary">About human review</p>
          <p className="text-[0.92rem] leading-7 text-on-surface/60">
            The Doctors tab keeps the profile card experience up front, but the HITL layer stays underneath it:
            AI comprehension, medication reminders, and doctor handoff history remain visible before any clinical action is taken.
          </p>
          <div className="mt-4 flex gap-3">
            <button className="flex h-10 w-10 items-center justify-center rounded-full bg-surface-container-lowest/75 text-tertiary">
              <Phone className="h-4 w-4" />
            </button>
            <button className="flex h-10 w-10 items-center justify-center rounded-full bg-surface-container-lowest/75 text-tertiary">
              <Brain className="h-4 w-4" />
            </button>
          </div>
        </SoftCard>
      </div>
    </motion.div>
  );
}
