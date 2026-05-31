import { useState } from 'react';
import { motion } from 'motion/react';
import { ChevronDown, FileHeart, MessageSquareHeart, Orbit, ShieldPlus, Ticket } from 'lucide-react';
import type { WorkspacePayload } from '../lib/api';
import { EmptyState, ErrorState, LoadingState } from '../components/States';
import { Pill, SectionShell, SoftCard } from '../components/ui';

function formatDate(value: string) {
  const date = new Date(value);
  return new Intl.DateTimeFormat('en-IN', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date);
}

export function HistoryScreen({
  workspace,
  loading,
  error,
}: {
  workspace: WorkspacePayload | null;
  loading: boolean;
  error: string | null;
}) {
  const [expandedSnapshotId, setExpandedSnapshotId] = useState<string | null>(null);
  if (loading && !workspace) return <LoadingState />;
  if (error && !workspace) return <ErrorState message={error} />;
  if (!workspace) return <EmptyState title="No history loaded" description="Once your workspace is available, this timeline will gather cases, prescriptions, messages, and stored memories." />;

  const timeline = [
    ...workspace.condition_snapshots.map((item) => ({
      id: `snapshot-${item.id}`,
      kind: 'Condition Snapshot',
      tone: 'sand' as const,
      title: item.snapshot_type.replaceAll('_', ' '),
      summary: item.summary,
      timestamp: item.created_at,
      link: null,
      icon: ShieldPlus,
      snapshot: item,
    })),
    ...workspace.cases.map((item) => ({
      id: `case-${item.id}`,
      kind: 'Doctor Case',
      tone: 'terracotta' as const,
      title: item.case_type.replaceAll('_', ' '),
      summary: item.summary,
      timestamp: item.created_at,
      link: item.external_ticket_url,
      icon: Ticket,
    })),
    ...workspace.prescriptions.map((item) => ({
      id: `prescription-${item.id}`,
      kind: 'Prescription',
      tone: 'sage' as const,
      title: item.medication_name,
      summary: item.instructions || item.review_status,
      timestamp: item.created_at,
      link: item.document_drive_file_url,
      icon: FileHeart,
    })),
    ...workspace.notifications.map((item) => ({
      id: `notification-${item.id}`,
      kind: 'Communication',
      tone: 'sand' as const,
      title: item.message_type,
      summary: item.body,
      timestamp: item.created_at,
      link: null,
      icon: MessageSquareHeart,
    })),
    ...workspace.memories.map((item) => ({
      id: `memory-${item.id}`,
      kind: 'Medical Memory',
      tone: 'sage' as const,
      title: `${item.source_type} • ${item.modality}`,
      summary: item.summary_text || 'Stored for future similarity retrieval.',
      timestamp: item.created_at,
      link: item.drive_file_url,
      icon: Orbit,
      snapshot: null,
    })),
  ].sort((left, right) => new Date(right.timestamp).getTime() - new Date(left.timestamp).getTime());

  return (
    <motion.div initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -18 }} className="space-y-8">
      <SectionShell
        eyebrow="History"
        title={
          <>
            Clinical context becomes a <span className="text-tertiary italic">story</span>, not a pile of records.
          </>
        }
        description="This timeline blends prescriptions, handoffs, stored memories, and patient communication into one editorial view that a caregiver or clinician can actually scan."
      />

      {timeline.length ? (
        <div className="relative max-w-4xl space-y-8 pl-10 md:pl-14">
          <div className="absolute bottom-0 left-4 top-3 w-[2px] rounded-full bg-gradient-to-b from-primary-fixed via-surface-container-high to-secondary-container/40" />
          {timeline.map((item, index) => (
            <div key={item.id} className="relative">
              <div className={`absolute -left-10 top-5 flex h-10 w-10 items-center justify-center rounded-full border-4 border-surface ${
                item.tone === 'terracotta'
                  ? 'bg-secondary-container/75 text-secondary'
                  : item.tone === 'sand'
                    ? 'bg-tertiary-container/35 text-tertiary'
                    : 'bg-primary-fixed/55 text-primary'
              }`}>
                <item.icon className="h-4 w-4" />
              </div>

              <motion.div
                initial={{ opacity: 0, x: -16 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.04 }}
              >
                <SoftCard className="group">
                  <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                    <div className="space-y-3">
                      <Pill tone={item.tone}>{item.kind}</Pill>
                      <div>
                        <h3 className="font-serif text-2xl transition-colors group-hover:text-primary">{item.title}</h3>
                        <p className="mt-1 text-xs uppercase tracking-[0.2em] text-on-surface/40">{formatDate(item.timestamp)}</p>
                      </div>
                    </div>
                    {item.link ? (
                      <a href={item.link} target="_blank" rel="noreferrer" className="text-sm text-primary hover:underline">
                        Open attachment
                      </a>
                    ) : null}
                  </div>
                  <p className="mt-4 text-sm leading-7 text-on-surface/65">{item.summary}</p>
                  {'snapshot' in item && item.snapshot ? (() => {
                    const snap: any = item.snapshot;
                    return (
                      <div className="mt-5">
                        <button
                          type="button"
                          aria-expanded={expandedSnapshotId === item.id}
                          onClick={() => setExpandedSnapshotId((current) => (current === item.id ? null : item.id))}
                          className="flex items-center gap-2 text-sm text-primary hover:underline"
                        >
                          <ChevronDown className={`h-4 w-4 transition-transform ${expandedSnapshotId === item.id ? 'rotate-180' : ''}`} />
                          <span>{expandedSnapshotId === item.id ? 'Hide snapshot details' : 'Show snapshot details'}</span>
                        </button>
                        {expandedSnapshotId === item.id ? (
                          <div className="mt-4 grid gap-4 rounded-[1.25rem] bg-surface-container-lowest/35 p-5">
                            <div>
                              <p className="text-xs uppercase tracking-[0.2em] text-on-surface/40">Profile</p>
                              <p className="mt-2 text-sm text-on-surface/65">
                                {snap.profile?.full_name ? String(snap.profile.full_name) : 'Profile context saved.'}
                                {snap.profile?.summary ? ` • ${String(snap.profile.summary)}` : ''}
                              </p>
                            </div>
                            <div>
                              <p className="text-xs uppercase tracking-[0.2em] text-on-surface/40">Conditions</p>
                              <p className="mt-2 text-sm text-on-surface/65">
                                {snap.conditions?.length
                                  ? snap.conditions.map((entry: any) => String(entry.name ?? entry.condition_type ?? 'Condition')).join(', ')
                                  : 'No condition records stored in this snapshot.'}
                              </p>
                            </div>
                            <div>
                              <p className="text-xs uppercase tracking-[0.2em] text-on-surface/40">Prescriptions</p>
                              <p className="mt-2 text-sm text-on-surface/65">
                                {snap.prescriptions?.length
                                  ? snap.prescriptions.map((entry: any) => String(entry.medication_name ?? 'Prescription')).join(', ')
                                  : 'No prescription records stored in this snapshot.'}
                              </p>
                            </div>
                            <div>
                              <p className="text-xs uppercase tracking-[0.2em] text-on-surface/40">Vitals</p>
                              <p className="mt-2 text-sm text-on-surface/65">
                                {snap.vitals?.length
                                  ? snap.vitals
                                      .map((entry: any) => String(entry.blood_pressure ?? entry.weight_kg ?? entry.heart_rate_bpm ?? 'Vital'))
                                      .join(', ')
                                  : 'No vitals captured with this snapshot.'}
                              </p>
                            </div>
                          </div>
                        ) : null}
                      </div>
                    );
                  })() : null}
                </SoftCard>
              </motion.div>
            </div>
          ))}
        </div>
      ) : (
        <EmptyState title="No timeline entries yet" description="As you create escalations, scan prescriptions, and store memories, this screen will bloom into a longitudinal care timeline." />
      )}
    </motion.div>
  );
}
