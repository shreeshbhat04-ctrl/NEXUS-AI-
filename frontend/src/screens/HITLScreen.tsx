import { useEffect, useMemo, useState } from 'react';
import { motion } from 'motion/react';
import {
  Bell,
  Brain,
  Clock,
  HeartPulse,
  Loader2,
  Phone,
  Plus,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  Stethoscope,
  UserRound,
} from 'lucide-react';
import {
  fetchHITLComprehension,
  fetchReminders,
  saveReminder,
  shaunImage,
  strangeImage,
  surgeonImage,
  type HITLComprehensionResponse,
  type Reminder,
  type WorkspacePayload,
} from '../lib/api';
import { EmptyState, LoadingState } from '../components/States';
import { Pill, SectionShell, SoftCard } from '../components/ui';
import { DoctorCard } from '../components/DoctorCard';

type DoctorProfile = {
  id: string;
  name: string;
  specialty: string;
  email: string;
  phone: string;
  casesClosed: number;
  consultingDays: number;
  trackedConditions: string[];
  image: string;
  focusNote: string;
};

const DOCTOR_PROFILES: DoctorProfile[] = [
  {
    id: 'strange',
    name: 'Dr. Stephen Strange',
    specialty: 'Neurology & Surgical Precision',
    email: 'stephen.strange@nexus_ai.com',
    phone: '+1 (555) 000-0000',
    casesClosed: 245,
    consultingDays: 85,
    trackedConditions: ['Neural Pathways', 'Surgical Recovery', 'Quantum Diagnostics'],
    image: strangeImage,
    focusNote: 'Specialist in complex neural interventions and high-stakes surgical oversight.',
  },
  {
    id: 'shaun',
    name: 'Dr. Shaun Murphy',
    specialty: 'Pediatrics & Diagnostic Genius',
    email: 'shaun.murphy@nexus_ai.com',
    phone: '+1 (555) 123-4567',
    casesClosed: 142,
    consultingDays: 45,
    trackedConditions: ['Congenital Anomalies', 'Neurodiversity Care', 'Precision Diagnostics'],
    image: shaunImage,
    focusNote: 'Best for unique diagnostic patterns, intricate physiological connections, and surgical planning.',
  },
  {
    id: 'thorne',
    name: 'Dr. Aris Thorne',
    specialty: 'Internal Medicine & Chronic Care',
    email: 'aris.thorne@nexus_ai.com',
    phone: '+1 (555) 987-6543',
    casesClosed: 89,
    consultingDays: 12,
    trackedConditions: ['Long-term Diabetes', 'Hypertension Sync'],
    image: surgeonImage,
    focusNote: 'Focused on long-term adherence, patient-centric routine design, and daily wellness monitoring.',
  },
];

function reviewStatusTone(status: string): 'sage' | 'sand' | 'terracotta' {
  if (status === 'approved') return 'sage';
  if (status === 'pending') return 'sand';
  return 'terracotta';
}

function conditionTone(type: string): 'sage' | 'sand' | 'terracotta' {
  return type === 'chronic' ? 'terracotta' : 'sage';
}

export function HITLScreen({
  workspace,
  loading,
  onRefresh,
  patientId,
}: {
  workspace: WorkspacePayload | null;
  loading: boolean;
  onRefresh: () => void;
  patientId: number;
}) {
  const [selectedDoctorId, setSelectedDoctorId] = useState(DOCTOR_PROFILES[0].id);
  const [comprehensionByDoctor, setComprehensionByDoctor] = useState<Record<string, HITLComprehensionResponse>>({});
  const [loadingDoctorId, setLoadingDoctorId] = useState<string | null>(null);
  const [reportError, setReportError] = useState<string | null>(null);

  const [reminders, setReminders] = useState<Reminder[]>([]);
  const [loadingReminders, setLoadingReminders] = useState(false);
  const [showReminderForm, setShowReminderForm] = useState(false);
  const [reminderMed, setReminderMed] = useState('');
  const [reminderTime, setReminderTime] = useState('08:00');
  const [savingReminder, setSavingReminder] = useState(false);
  const [useCustomReminderMed, setUseCustomReminderMed] = useState(false);

  if (loading && !workspace) return <LoadingState />;
  if (!workspace) {
    return (
      <EmptyState
        title="No patient context yet"
        description="Log in or seed a patient before opening the doctors workspace."
      />
    );
  }

  const selectedDoctor = DOCTOR_PROFILES.find((doctor) => doctor.id === selectedDoctorId) ?? DOCTOR_PROFILES[0];
  const activeComprehension = comprehensionByDoctor[selectedDoctor.id] ?? null;
  const medOptions = workspace.prescriptions.map((prescription) => prescription.medication_name);
  const doctorCases = workspace.cases.filter((item) => item.case_type === 'doctor_review').slice(0, 3);

  const runComprehension = async (doctorId: string) => {
    try {
      setSelectedDoctorId(doctorId);
      setLoadingDoctorId(doctorId);
      setReportError(null);
      const result = await fetchHITLComprehension(patientId);
      setComprehensionByDoctor((current) => ({ ...current, [doctorId]: result }));
    } catch (error) {
      setReportError(error instanceof Error ? error.message : 'Failed to generate doctor brief.');
    } finally {
      setLoadingDoctorId(null);
    }
  };

  const loadReminders = async () => {
    try {
      setLoadingReminders(true);
      const result = await fetchReminders(patientId);
      setReminders(result.reminders);
    } catch {
      // Keep the reminders panel quiet on read failure.
    } finally {
      setLoadingReminders(false);
    }
  };

  const handleReminderMedicationChange = (value: string) => {
    if (value === '__custom') {
      setUseCustomReminderMed(true);
      setReminderMed('');
      return;
    }

    setUseCustomReminderMed(false);
    setReminderMed(value);
  };

  const handleSaveReminder = async () => {
    if (!reminderMed.trim() || !reminderTime) return;

    try {
      setSavingReminder(true);
      await saveReminder(patientId, reminderMed.trim(), reminderTime);
      setReminderMed('');
      setReminderTime('08:00');
      setUseCustomReminderMed(false);
      setShowReminderForm(false);
      await loadReminders();
    } catch {
      // Keep the panel calm for now; the rest of the screen stays usable.
    } finally {
      setSavingReminder(false);
    }
  };

  useEffect(() => {
    void loadReminders();
  }, [patientId]);

  const overviewStats = useMemo(
    () => [
      { label: 'Doctor profiles', value: DOCTOR_PROFILES.length.toString() },
      { label: 'Doctor handoffs', value: workspace.cases.filter((item) => item.case_type === 'doctor_review').length.toString() },
      { label: 'Medication reminders', value: reminders.length.toString() },
    ],
    [reminders.length, workspace.cases],
  );

  return (
    <motion.div
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -18 }}
      className="space-y-8"
    >
      <SectionShell
        eyebrow="Doctors"
        title={
          <>
            Doctor <span className="text-primary italic">profiles</span> with AI comprehension.
          </>
        }
        description="Choose the clinician view you want, generate a doctor-ready patient brief for that profile, and keep reminders plus human review history in the same workspace."
      />

      {reportError ? (
        <p className="rounded-[1.25rem] bg-secondary-container/30 px-4 py-3 text-sm leading-7 text-secondary">
          {reportError}
        </p>
      ) : null}

      <div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <div className="space-y-6">
          <div className="grid gap-6 lg:grid-cols-2">
            {DOCTOR_PROFILES.map((doctor) => {
              const isSelected = doctor.id === selectedDoctor.id;
              const hasBrief = Boolean(comprehensionByDoctor[doctor.id]);
              const isLoading = loadingDoctorId === doctor.id;

              return (
                <DoctorCard
                  key={doctor.id}
                  doctor={doctor}
                  isSelected={isSelected}
                  hasBrief={hasBrief}
                  isLoading={isLoading}
                  onSelect={setSelectedDoctorId}
                  onGenerate={runComprehension}
                />
              );
            })}
          </div>

          <SoftCard className="bg-[linear-gradient(135deg,rgba(66,133,244,0.04),rgba(66,133,244,0.08))]">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-[0.72rem] font-semibold uppercase tracking-[0.2em] text-primary/75">Selected doctor</p>
                <h2 className="mt-2 font-serif text-[1.85rem] leading-tight">{selectedDoctor.name}</h2>
                <p className="mt-2 max-w-2xl text-[0.98rem] leading-8 text-on-surface/65">
                  {selectedDoctor.specialty}. The AI comprehension below is framed for this profile so the doctor handoff stays readable and specific.
                </p>
              </div>
              <button
                onClick={onRefresh}
                className="river-stone-btn flex items-center gap-2 bg-surface-container-low px-4 py-3 text-sm text-on-surface/72 hover:bg-surface-container-high"
              >
                <RefreshCw className="h-4 w-4" />
                Refresh patient context
              </button>
            </div>
          </SoftCard>

          {activeComprehension ? (
            <div className="space-y-6">
              <SoftCard>
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <p className="text-[0.72rem] font-semibold uppercase tracking-[0.2em] text-primary/75">AI doctor brief</p>
                    <h3 className="mt-2 font-serif text-2xl">Patient overview for {selectedDoctor.name}</h3>
                  </div>
                  <div className="rounded-full bg-primary-fixed/45 p-3 text-primary">
                    <Brain className="h-5 w-5" />
                  </div>
                </div>

                <div className="mt-5 grid gap-4 md:grid-cols-2">
                  <div className="soft-panel">
                    <p className="text-[0.72rem] uppercase tracking-[0.18em] text-on-surface/45">Patient</p>
                    <p className="mt-1 text-[1.05rem] font-medium">{activeComprehension.patient.name}</p>
                  </div>
                  <div className="soft-panel">
                    <p className="text-[0.72rem] uppercase tracking-[0.18em] text-on-surface/45">Date of birth</p>
                    <p className="mt-1 text-[1.05rem] font-medium">
                      {activeComprehension.patient.dob || 'Not recorded'}
                    </p>
                  </div>
                </div>

                <div className="mt-4 rounded-[1.3rem] bg-surface-container-low px-5 py-4">
                  <p className="text-[0.72rem] uppercase tracking-[0.18em] text-on-surface/45">Clinical summary</p>
                  <p className="mt-2 text-sm leading-7 text-on-surface/65">
                    {activeComprehension.patient.summary || 'No summary available yet.'}
                  </p>
                </div>
              </SoftCard>

              <SoftCard>
                <div className="flex items-center gap-3 text-primary">
                  <ShieldCheck className="h-5 w-5" />
                  <h3 className="font-serif text-xl">Active conditions</h3>
                </div>
                <div className="mt-4 space-y-3">
                  {activeComprehension.conditions.length > 0 ? (
                    activeComprehension.conditions.map((condition) => (
                      <div key={`${condition.name}-${condition.last_updated ?? 'unknown'}`} className="soft-panel">
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <p className="font-medium">{condition.name}</p>
                            <p className="mt-1 text-sm leading-7 text-on-surface/58">
                              {condition.notes || 'No notes recorded.'}
                            </p>
                          </div>
                          <div className="shrink-0 text-right">
                            <Pill tone={conditionTone(condition.type)}>{condition.type}</Pill>
                            <p className="mt-1 text-[0.74rem] text-on-surface/45">
                              {condition.last_updated || 'Update pending'}
                            </p>
                          </div>
                        </div>
                      </div>
                    ))
                  ) : (
                    <p className="text-sm leading-7 text-on-surface/55">No conditions recorded.</p>
                  )}
                </div>
              </SoftCard>

              <SoftCard>
                <div className="flex items-center gap-3 text-secondary">
                  <HeartPulse className="h-5 w-5" />
                  <h3 className="font-serif text-xl">Medications and duration</h3>
                </div>
                <div className="mt-4 space-y-3">
                  {activeComprehension.medications.length > 0 ? (
                    activeComprehension.medications.map((medication) => (
                      <div key={medication.name} className="soft-panel">
                        <div className="flex items-center justify-between gap-3">
                          <p className="text-[1rem] font-medium">{medication.name}</p>
                          <Pill tone={reviewStatusTone(medication.review_status)}>{medication.review_status}</Pill>
                        </div>
                        <div className="mt-3 grid gap-3 md:grid-cols-3">
                          <div>
                            <p className="text-[0.72rem] uppercase tracking-[0.18em] text-on-surface/40">Dosage</p>
                            <p className="mt-1 text-sm">{medication.dosage || '--'}</p>
                          </div>
                          <div>
                            <p className="text-[0.72rem] uppercase tracking-[0.18em] text-on-surface/40">Days on med</p>
                            <p className="mt-1 text-sm font-semibold text-primary">
                              {medication.days_on_medication ?? '--'}
                            </p>
                          </div>
                          <div>
                            <p className="text-[0.72rem] uppercase tracking-[0.18em] text-on-surface/40">Confidence</p>
                            <p className="mt-1 text-sm">{(medication.confidence_score * 100).toFixed(0)}%</p>
                          </div>
                        </div>
                        {medication.instructions ? (
                          <p className="mt-2 text-sm leading-7 text-on-surface/58">{medication.instructions}</p>
                        ) : null}
                      </div>
                    ))
                  ) : (
                    <p className="text-sm leading-7 text-on-surface/55">No medications recorded.</p>
                  )}
                </div>
              </SoftCard>

              <SoftCard className="bg-[linear-gradient(135deg,rgba(66,133,244,0.04),rgba(66,133,244,0.08))]">
                <div className="flex items-center gap-3 text-primary">
                  <Sparkles className="h-5 w-5" />
                  <h3 className="font-serif text-xl">AI analysis and next steps</h3>
                </div>
                <div className="mt-4 whitespace-pre-wrap text-[0.95rem] leading-8 text-on-surface/75">
                  {activeComprehension.ai_analysis}
                </div>
                <div className="mt-4">
                  <Pill tone="sage">Doctor-facing comprehension ready</Pill>
                </div>
              </SoftCard>
            </div>
          ) : (
            <SoftCard className="bg-surface-container-low">
              <div className="flex flex-col items-center gap-4 py-10 text-center">
                <div className="rounded-full bg-primary-fixed/35 p-5 text-primary">
                  <Stethoscope className="h-8 w-8" />
                </div>
                <div>
                  <h3 className="font-serif text-xl">No doctor brief generated yet</h3>
                  <p className="mt-2 max-w-2xl text-sm leading-7 text-on-surface/55">
                    Use one of the doctor profile cards above to generate an AI comprehension brief without losing the existing HITL workflow.
                  </p>
                </div>
              </div>
            </SoftCard>
          )}
        </div>

        <div className="space-y-6">
          <SoftCard className="bg-secondary-container/18">
            <div className="flex items-center gap-3 text-secondary">
              <UserRound className="h-5 w-5" />
              <h3 className="font-serif text-xl">Doctors overview</h3>
            </div>
            <div className="mt-5 grid gap-3 sm:grid-cols-3 xl:grid-cols-1">
              {overviewStats.map((stat) => (
                <div key={stat.label} className="rounded-[1.3rem] bg-surface-container-lowest/70 px-4 py-4">
                  <p className="text-[0.72rem] uppercase tracking-[0.18em] text-on-surface/45">{stat.label}</p>
                  <p className="mt-1 text-[1.35rem] font-semibold text-on-surface">{stat.value}</p>
                </div>
              ))}
            </div>
            <p className="mt-5 text-sm leading-7 text-on-surface/65">
              {selectedDoctor.name} is the active review profile. Generate or refresh the AI comprehension whenever you want a fresh doctor-facing readout.
            </p>
          </SoftCard>

          <SoftCard>
            <div className="flex items-center justify-between gap-4">
              <div className="flex items-center gap-3 text-secondary">
                <Bell className="h-5 w-5" />
                <h3 className="font-serif text-xl">Medication reminders</h3>
              </div>
              <button
                onClick={() => setShowReminderForm((current) => !current)}
                className="flex h-10 w-10 items-center justify-center rounded-full bg-secondary-container/40 text-secondary transition-colors hover:bg-secondary-container/60"
              >
                <Plus className="h-5 w-5" />
              </button>
            </div>

            {showReminderForm ? (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="mt-4 space-y-4 rounded-[1.5rem] bg-surface-container-low px-5 py-5"
              >
                <label className="space-y-2">
                  <span className="text-sm font-medium text-on-surface/60">Medication</span>
                  {medOptions.length > 0 ? (
                    <>
                      <select
                        value={useCustomReminderMed ? '__custom' : reminderMed}
                        onChange={(event) => handleReminderMedicationChange(event.target.value)}
                        className="input-shell"
                      >
                        <option value="">Select medication...</option>
                        {medOptions.map((medication) => (
                          <option key={medication} value={medication}>
                            {medication}
                          </option>
                        ))}
                        <option value="__custom">Other (type below)</option>
                      </select>
                      {useCustomReminderMed ? (
                        <input
                          value={reminderMed}
                          onChange={(event) => setReminderMed(event.target.value)}
                          placeholder="Enter medication name"
                          className="input-shell"
                        />
                      ) : null}
                    </>
                  ) : (
                    <input
                      value={reminderMed}
                      onChange={(event) => setReminderMed(event.target.value)}
                      placeholder="e.g. Metformin"
                      className="input-shell"
                    />
                  )}
                </label>

                <label className="space-y-2">
                  <span className="text-sm font-medium text-on-surface/60">Reminder time</span>
                  <input
                    type="time"
                    value={reminderTime}
                    onChange={(event) => setReminderTime(event.target.value)}
                    className="input-shell"
                  />
                </label>

                <button
                  onClick={handleSaveReminder}
                  disabled={savingReminder || !reminderMed.trim() || !reminderTime}
                  className="river-stone-btn w-full bg-gradient-to-br from-secondary to-secondary-container px-6 py-3 text-surface disabled:opacity-50"
                >
                  {savingReminder ? (
                    <span className="flex items-center justify-center gap-2">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Saving reminder...
                    </span>
                  ) : (
                    <span className="flex items-center justify-center gap-2">
                      <Clock className="h-4 w-4" />
                      Set reminder
                    </span>
                  )}
                </button>
              </motion.div>
            ) : null}

            <div className="mt-5 space-y-3">
              {loadingReminders ? (
                <p className="text-sm text-on-surface/45">Loading reminders...</p>
              ) : reminders.length > 0 ? (
                reminders.map((reminder) => (
                  <div
                    key={reminder.id}
                    className="flex items-center justify-between gap-3 rounded-[1.25rem] bg-surface-container-low px-4 py-3"
                  >
                    <div className="flex items-center gap-3">
                      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-secondary-container/30 text-secondary">
                        <Clock className="h-4 w-4" />
                      </div>
                      <div>
                        <p className="text-[0.95rem] font-medium">{reminder.medication_name}</p>
                        <p className="text-[0.82rem] text-on-surface/50">
                          Every day at <span className="font-semibold text-secondary">{reminder.reminder_time}</span>
                        </p>
                      </div>
                    </div>
                    <Pill tone="sage">Active</Pill>
                  </div>
                ))
              ) : (
                <p className="text-sm leading-7 text-on-surface/55">
                  No reminders set yet. Use the plus button to add the first one.
                </p>
              )}
            </div>
          </SoftCard>

          <SoftCard>
            <div className="flex items-center gap-3 text-primary">
              <Stethoscope className="h-5 w-5" />
              <h3 className="font-serif text-xl">Recent doctor handoffs</h3>
            </div>
            <div className="mt-4 space-y-3">
              {doctorCases.length > 0 ? (
                doctorCases.map((item) => (
                  <div key={item.id} className="soft-panel">
                    <div className="flex items-center justify-between gap-3">
                      <p className="font-medium">Doctor review case #{item.id}</p>
                      <Pill tone={item.status === 'open' ? 'terracotta' : 'sage'}>{item.status}</Pill>
                    </div>
                    <p className="mt-2 text-sm leading-7 text-on-surface/58">{item.summary}</p>
                  </div>
                ))
              ) : (
                <p className="text-sm leading-7 text-on-surface/55">
                  No doctor review cases have been created yet.
                </p>
              )}
            </div>
          </SoftCard>


        </div>
      </div>
    </motion.div>
  );
}
