import { useState } from 'react';
import { motion } from 'motion/react';
import { ChevronDown, HeartPulse, Stethoscope, TimerReset } from 'lucide-react';
import type { WorkspacePayload } from '../../shared/lib/api';
import { ErrorState, LoadingState } from '../../shared/components/States';
import { Pill, SectionShell } from '../../shared/components/ui';

const DATE_ONLY_PATTERN = /^\d{4}-\d{2}-\d{2}$/;

function formatRoutineDueDate(dueAt?: string | null, dueOn?: string | null) {
  if (!dueAt) return dueOn;

  if (DATE_ONLY_PATTERN.test(dueAt)) {
    const [year, month, day] = dueAt.split('-').map(Number);
    return new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium' }).format(new Date(year, month - 1, day));
  }

  return new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(dueAt));
}

export function DashboardScreen({
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
  const [expandedTaskId, setExpandedTaskId] = useState<string | null>(null);
  if (loading && !workspace) return <LoadingState />;
  if (error && !workspace) return <ErrorState message={error} onRetry={onRefresh} />;
  if (!workspace) return <ErrorState message="No workspace loaded." onRetry={onRefresh} />;

  const { patient, conditions, checkin, prescriptions, cases } = workspace;
  const latestCase = cases[0];
  const latestPrescription = prescriptions[0];

  return (
    <motion.div initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -18 }} className="space-y-8 pb-12">
      <SectionShell
        eyebrow="Dashboard"
        title={
          <>
            Good evening, <span className="text-primary italic font-serif">{patient.full_name.split(' ')[0]}</span>.
          </>
        }
        description={checkin.message}
      />

      <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <div className="glass-panel relative overflow-hidden rounded-[1.25rem] p-8 text-on-surface group transition-all duration-300">
          <div className="absolute right-[-3rem] top-[-3rem] h-48 w-48 rounded-full bg-primary-fixed/30 blur-3xl" />
          <div className="relative z-10 space-y-8">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="eyebrow text-primary/70">Sanctuary pulse</p>
                <h2 className="mt-4 font-serif text-[2.1rem] leading-tight tracking-[-0.02em] xl:text-[2.4rem] text-on-surface">Care is coordinated and visible.</h2>
              </div>
              <div className="rounded-2xl bg-surface-container-lowest/60 p-4 glass-edge">
                <HeartPulse className="h-7 w-7 text-primary" />
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-3">
              <div className="rounded-[1.25rem] bg-[#e8f0fe] px-6 py-5">
                <p className="eyebrow text-[#1a73e8]">Conditions</p>
                <p className="mt-3 text-[2.2rem] font-sans font-bold text-on-surface">{conditions.length}</p>
              </div>
              <div className="rounded-[1.25rem] bg-[#e6f4ea] px-6 py-5">
                <p className="eyebrow text-[#34a853]">Routines</p>
                <p className="mt-3 text-[2.2rem] font-sans font-bold text-on-surface">{checkin.routine_tasks.length}</p>
              </div>
              <div className="rounded-[1.25rem] bg-[#fef7e0] px-6 py-5">
                <p className="eyebrow text-[#f9ab00]">Doctor cases</p>
                <p className="mt-3 text-[2.2rem] font-sans font-bold text-on-surface">{cases.length}</p>
              </div>
            </div>
          </div>
        </div>

        <div className="glass-panel rounded-[1.25rem] p-8">
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="eyebrow text-primary/70">Latest handoff</p>
              <h2 className="mt-4 font-serif text-[1.8rem] leading-tight text-on-surface">Doctor-ready context</h2>
            </div>
            <div className="rounded-2xl bg-surface-container-lowest/40 p-4 glass-edge">
              <Stethoscope className="h-6 w-6 text-primary" />
            </div>
          </div>

          <div className="mt-8 space-y-6">
            {latestCase ? (
              <>
                <Pill>{latestCase.status}</Pill>
                <p className="text-[1.02rem] leading-8 text-on-surface/80 font-sans">{latestCase.summary}</p>
                <div className="flex flex-wrap gap-4 text-[0.9rem] text-primary">
                  {latestCase.external_ticket_url ? <a className="hover:underline" href={latestCase.external_ticket_url} target="_blank" rel="noreferrer">Asana case</a> : null}
                  {latestCase.calendar_event_url ? <a className="hover:underline" href={latestCase.calendar_event_url} target="_blank" rel="noreferrer">Follow-up event</a> : null}
                  {latestCase.drive_file_url ? <a className="hover:underline" href={latestCase.drive_file_url} target="_blank" rel="noreferrer">Supporting document</a> : null}
                </div>
              </>
            ) : (
              <p className="text-[1rem] leading-7 text-on-surface/50 font-sans">No live escalation case yet. The room is calm for now.</p>
            )}
          </div>
        </div>
      </div>

      <div className="grid gap-6">
        <div className="glass-panel rounded-[1.25rem] p-8">
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="eyebrow text-on-surface/50">Daily rhythm</p>
              <h2 className="mt-4 font-serif text-[1.8rem] leading-tight text-on-surface">Routine blossoms</h2>
            </div>
            <div className="rounded-2xl bg-surface-container-lowest/40 p-4 glass-edge">
              <TimerReset className="h-6 w-6 text-on-surface/40" />
            </div>
          </div>

          <div className="mt-8 grid gap-4 md:grid-cols-2">
            {checkin.routine_tasks.slice(0, 4).map((task) => {
              const formattedDue = formatRoutineDueDate(task.due_at, task.due_on);

              return (
                <div key={task.task_id} className="rounded-[1.25rem] bg-surface-container-lowest/30 p-6 glass-edge">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-[1.1rem] font-bold text-on-surface font-serif">{task.title || task.name}</p>
                    <p className="mt-2 text-[0.95rem] leading-7 text-on-surface/60 font-sans">
                      {task.short_summary || task.notes || 'No extra notes attached to this rhythm yet.'}
                    </p>
                    <div className="mt-3 flex flex-wrap items-center gap-3 text-xs uppercase tracking-[0.18em] text-on-surface/40">
                      <span>{task.source || 'Routine'}</span>
                      {formattedDue ? <span>Due {formattedDue}</span> : null}
                      {task.assignee_name ? <span>{task.assignee_name}</span> : null}
                    </div>
                  </div>
                  <Pill tone={task.completed ? 'sage' : 'terracotta'}>{task.completed ? 'Done' : 'Open'}</Pill>
                </div>
                <div className="mt-4 flex flex-wrap items-center gap-4">
                  <button
                    type="button"
                    aria-expanded={expandedTaskId === task.task_id}
                    onClick={() => setExpandedTaskId((current) => (current === task.task_id ? null : task.task_id))}
                    className="flex items-center gap-2 text-sm text-primary hover:underline"
                  >
                    <ChevronDown className={`h-4 w-4 transition-transform ${expandedTaskId === task.task_id ? 'rotate-180' : ''}`} />
                    <span>{expandedTaskId === task.task_id ? 'Hide details' : 'View details'}</span>
                  </button>
                  {task.permalink_url ? (
                    <a href={task.permalink_url} target="_blank" rel="noreferrer" className="text-sm text-primary hover:underline">
                      Open source
                    </a>
                  ) : null}
                </div>
                {expandedTaskId === task.task_id ? (
                  <div className="mt-4 rounded-[1rem] bg-surface-container-lowest/45 p-4 text-sm leading-7 text-on-surface/70">
                    {task.full_details || task.notes || 'No additional detail was provided for this routine item.'}
                  </div>
                ) : null}
                </div>
              );
            })}
          </div>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-1">
        <div className="glass-panel rounded-[1.25rem] p-8 relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-r from-primary/5 to-transparent" />
          <h3 className="font-serif text-[1.5rem] text-primary relative z-10">Latest medication</h3>
          <p className="mt-4 text-[1.15rem] font-bold text-on-surface relative z-10 font-serif">{latestPrescription?.medication_name ?? 'No scanned prescription yet'}</p>
          <p className="mt-2 text-[1rem] leading-7 text-on-surface/60 font-sans relative z-10">{latestPrescription?.instructions ?? 'Upload a prescription to turn this into a live medication card.'}</p>
        </div>
      </div>
    </motion.div>
  );
}
