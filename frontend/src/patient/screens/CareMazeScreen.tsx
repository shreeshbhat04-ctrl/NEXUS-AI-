import { useRef, useState } from 'react';
import { motion } from 'motion/react';
import {
  CheckCircle2,
  Loader2,
  MapPinned,
  Route,
  Sparkles,
  Stethoscope,
  Upload,
  Waves,
} from 'lucide-react';
import {
  createCalendarEvent,
  createEscalation,
  fetchDietSupport,
  sendTextMessage,
  uploadAndAnalyzeVision,
  type DietSupportResponse,
  type VisionUploadAnalyzeResponse,
  type WorkspacePayload,
} from '../../shared/lib/api';
import { EmptyState, LoadingState } from '../../shared/components/States';
import { Pill, SectionShell, SoftCard } from '../../shared/components/ui';

type BusyAction = 'maze' | 'calendar' | 'escalate' | 'location' | 'followup' | 'doctor-chat';

const DEMO_BEATS = [
  {
    title: 'One patient, many specialists',
    body: 'The demo follows a patient with epilepsy and atopic eczema who is now dealing with fever and back pain across multiple doctors.',
  },
  {
    title: 'Symptoms stay attached to the record',
    body: 'Uploads, prescriptions, and symptom images move through the same care path so the doctor sees the before and after context together.',
  },
  {
    title: 'Nothing is left blank',
    body: 'When live data is missing, the backend still returns a hardcoded preview so the presentation keeps moving instead of stopping on an empty state.',
  },
];

function isValidHttpUrl(url: string) {
  try {
    const parsed = new URL(url);
    return parsed.protocol === 'http:' || parsed.protocol === 'https:';
  } catch {
    return false;
  }
}

export function CareMazeScreen({
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
  const [medicationName, setMedicationName] = useState('Metformin');
  const [supportResult, setSupportResult] = useState<DietSupportResponse | null>(null);
  const [busyAction, setBusyAction] = useState<BusyAction | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [visionResult, setVisionResult] = useState<VisionUploadAnalyzeResponse | null>(null);
  const busyActionRef = useRef<BusyAction | null>(null);
  const isDemoSource = (sourceUsed?: string | null) => Boolean(sourceUsed && sourceUsed !== 'google_maps_places_text_search');

  if (loading && !workspace) return <LoadingState />;
  if (!workspace) {
    return (
      <EmptyState
        title="No workspace yet"
        description="Create or seed a patient profile before opening the care maze."
      />
    );
  }

  const primaryDoctor = workspace.doctors.find((doctor) => doctor.is_default) ?? workspace.doctors[0] ?? null;
  const primaryCondition = workspace.conditions[0]?.name ?? null;
  const latestCase = workspace.cases[0];
  const isBusy = Boolean(busyAction);
  const disabledButtonClass = 'disabled:cursor-not-allowed disabled:opacity-60';

  const startBusyAction = (action: BusyAction) => {
    if (busyActionRef.current || busyAction) return false;

    busyActionRef.current = action;
    setBusyAction(action);
    return true;
  };

  const clearBusyAction = () => {
    busyActionRef.current = null;
    setBusyAction(null);
  };

  const runMaze = async () => {
    if (!startBusyAction('maze')) return;

    try {
      setFeedback(null);
      const result = await fetchDietSupport(
        patientId,
        medicationName,
        'Home'
      );
      setSupportResult(result);
      setFeedback('Diet Support generated.');
    } catch (error) {
      setFeedback(error instanceof Error ? error.message : 'Unable to get support plan right now.');
    } finally {
      clearBusyAction();
    }
  };

  const scheduleFollowUp = async () => {
    if (!startBusyAction('calendar')) return;

    try {
      const result = await createCalendarEvent(patientId, 'Care Maze follow-up');
      setFeedback(result.html_link ? 'Calendar follow-up created successfully.' : 'Calendar event created.');
      await onRefresh();
    } catch (error) {
      setFeedback(error instanceof Error ? error.message : 'Unable to create the follow-up event.');
    } finally {
      clearBusyAction();
    }
  };

  const createDoctorHandoff = async () => {
    if (!startBusyAction('escalate')) return;

    try {
      const summary = visionResult
        ? `Care Maze review requested after ${visionResult.category.toLowerCase()} upload. ${visionResult.summary}`
        : `Care Maze review requested for ${medicationName} around ${'Home'}.`;
      const result = await createEscalation(
        patientId,
        summary,
        'Care Maze',
        primaryDoctor?.id ?? null,
      );
      setFeedback(result.external_ticket_url ? 'Doctor handoff created and sent to Asana.' : 'Escalation case created.');
      await onRefresh();
    } catch (error) {
      setFeedback(error instanceof Error ? error.message : 'Unable to create the doctor handoff.');
    } finally {
      clearBusyAction();
    }
  };

  const handleFileSelect = async (file: File) => {
    setSelectedFile(file);
    setVisionResult(null);
    if (file.type.startsWith('image/')) {
      setPreviewUrl(URL.createObjectURL(file));
    } else {
      setPreviewUrl(null);
    }

    setAnalyzing(true);
    try {
      const result = await uploadAndAnalyzeVision(patientId, file, {
        doctorId: primaryDoctor?.id ?? null,
        diseaseName: primaryCondition ?? medicationName,
        captureDate: new Date().toISOString().slice(0, 10),
      });
      setVisionResult(result);
      setFeedback(`Vision workflow completed and saved to Drive as ${result.drive_upload.file_name}.`);
      await onRefresh();
    } catch (error) {
      setFeedback(error instanceof Error ? error.message : 'The upload could not be analysed right now.');
    } finally {
      setAnalyzing(false);
    }
  };

  const askFollowUp = async () => {
    if (!visionResult) return;
    try {
      setBusyAction('followup');
      const response = await sendTextMessage(
        patientId,
        `I uploaded a ${visionResult.category.toLowerCase()} image. Summary: ${visionResult.summary} Please ask the best follow-up question.`,
      );
      setFeedback(response.message);
    } catch (error) {
      setFeedback(error instanceof Error ? error.message : 'Unable to prepare a follow-up question.');
    } finally {
      setBusyAction(null);
    }
  };

  const chatWithDoctor = async () => {
    if (!visionResult) return;
    try {
      setBusyAction('doctor-chat');
      const response = await sendTextMessage(
        patientId,
        `Help me prepare a short doctor chat about this upload: ${visionResult.summary}. Mention ${primaryDoctor?.full_name ?? 'my doctor'}.`,
      );
      setFeedback(response.message);
    } catch (error) {
      setFeedback(error instanceof Error ? error.message : 'Unable to prepare the doctor chat context.');
    } finally {
      setBusyAction(null);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file) void handleFileSelect(file);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -18 }}
      className="space-y-8"
    >
      <SectionShell
        eyebrow="Care Maze"
        title={
          <>
            Navigate the <span className="text-secondary italic">gaps</span> before they become friction.
          </>
        }
        description="This view now pulls care destinations, route hints, live upload analysis, dietary support, and doctor escalation into one backend-driven care route."
      />

      <SoftCard className="bg-surface-container-low">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="max-w-3xl space-y-3">
            <p className="text-xs uppercase tracking-[0.2em] text-primary/75">Demo briefing</p>
            <h2 className="font-serif text-3xl leading-tight">A presenter-friendly version of the care maze.</h2>
            <p className="text-sm leading-7 text-on-surface/65">
              This panel is intentionally dense so judges see the story immediately: cross-doctor care, medication overlap, symptom analysis, and a route to escalation without leaving the screen empty.
            </p>
          </div>
          <div className="rounded-full bg-primary-fixed/45 px-4 py-2 text-sm font-medium text-primary">
            Live demo mode
          </div>
        </div>

        <div className="mt-6 grid gap-4 lg:grid-cols-3">
          {DEMO_BEATS.map((beat) => (
            <div key={beat.title} className="rounded-[1.4rem] bg-surface px-5 py-4">
              <p className="font-serif text-[1.05rem] text-on-surface">{beat.title}</p>
              <p className="mt-2 text-sm leading-7 text-on-surface/60">{beat.body}</p>
            </div>
          ))}
        </div>
      </SoftCard>

      <div className="grid gap-6 xl:grid-cols-[1.08fr_0.92fr]">
        <SoftCard className="space-y-6">
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="text-xs uppercase tracking-[0.2em] text-secondary/75">Video Studio</p>
              <h2 className="mt-2 font-serif text-2xl">Veo Video Generation</h2>
            </div>
            <div className="rounded-full bg-secondary-container/30 p-3 text-secondary">
              <Route className="h-5 w-5" />
            </div>
          </div>

          <div className="space-y-4">
            <label className="space-y-2">
              <span className="text-sm font-medium text-on-surface/60">Medication focus</span>
              <input value={medicationName} onChange={(e) => setMedicationName(e.target.value)} className="input-shell" />
            </label>
          </div>

          <div className="flex flex-wrap gap-3">
            <button
              onClick={runMaze}
              disabled={isBusy}
              className={`river-stone-btn bg-linear-to-br from-primary to-primary-container px-6 py-4 text-surface ${disabledButtonClass}`}
            >
              {busyAction === 'maze' ? 'Generating...' : 'Generate Veo Video'}
            </button>
          </div>

          <div className="flex flex-wrap gap-2">
            {primaryDoctor ? <Pill>{primaryDoctor.full_name}</Pill> : null}
            {primaryCondition ? <Pill tone="sand">{primaryCondition}</Pill> : null}
          </div>

          {feedback ? (
            <p className="rounded-[1.25rem] bg-surface-container-low px-4 py-3 text-sm leading-7 text-on-surface/70">
              {feedback}
            </p>
          ) : null}
        </SoftCard>

        <SoftCard className="bg-surface-container-low">
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="text-xs uppercase tracking-[0.2em] text-tertiary/75">Live coordination</p>
              <h2 className="mt-2 font-serif text-2xl">Latest care handoff</h2>
            </div>
            <div className="rounded-full bg-tertiary-container/18 p-3 text-tertiary">
              <Stethoscope className="h-5 w-5" />
            </div>
          </div>
          <div className="mt-6 space-y-4">
            {latestCase ? (
              <>
                <Pill tone="terracotta">{latestCase.status}</Pill>
                <p className="text-sm leading-7 text-on-surface/68">{latestCase.summary}</p>
                <div className="space-y-2 text-sm text-on-surface/55">
                  {latestCase.pharmacy_search_summary ? (
                    <p>
                      <span className="font-medium text-on-surface/70">Nearby pharmacies:</span>{' '}
                      {latestCase.pharmacy_search_summary}
                    </p>
                  ) : null}
                  {latestCase.external_ticket_url && isValidHttpUrl(latestCase.external_ticket_url) ? (
                    <a href={latestCase.external_ticket_url} target="_blank" rel="noreferrer" className="block hover:text-primary">
                      Open Asana case
                    </a>
                  ) : latestCase.external_ticket_url ? (
                    <p className="break-all">{latestCase.external_ticket_url}</p>
                  ) : null}
                  {latestCase.calendar_event_url && isValidHttpUrl(latestCase.calendar_event_url) ? (
                    <a href={latestCase.calendar_event_url} target="_blank" rel="noreferrer" className="block hover:text-primary">
                      Open follow-up in Calendar
                    </a>
                  ) : latestCase.calendar_event_url ? (
                    <p className="break-all">{latestCase.calendar_event_url}</p>
                  ) : null}
                </div>
              </>
            ) : (
              <p className="text-sm leading-7 text-on-surface/60">
                No live handoff yet. Use the actions on the left to create one from this screen.
              </p>
            )}
          </div>
        </SoftCard>
      </div>

      <SoftCard className="space-y-6">
        <div className="flex items-center justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-primary/75">Unified vision flow</p>
            <h2 className="mt-2 font-serif text-2xl">Upload once, analyze and save everywhere</h2>
          </div>
          <div className="rounded-full bg-primary-fixed/45 p-3 text-primary">
            <Sparkles className="h-5 w-5" />
          </div>
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          <div className="space-y-4">
            <div
              onDragOver={(e) => {
                e.preventDefault();
                setIsDragOver(true);
              }}
              onDragLeave={() => setIsDragOver(false)}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`flex cursor-pointer flex-col items-center gap-3 rounded-[1.75rem] border-2 border-dashed px-6 py-10 transition-all duration-200 ${
                isDragOver
                  ? 'border-primary bg-primary-fixed/20'
                  : 'border-outline-variant/40 bg-surface-container-low hover:border-primary/40 hover:bg-surface-container-high/60'
              }`}
            >
              <Upload className={`h-8 w-8 ${isDragOver ? 'text-primary' : 'text-on-surface/35'}`} />
              <div className="text-center">
                <p className="text-[0.95rem] font-medium text-on-surface/70">
                  {selectedFile ? selectedFile.name : 'Drop a medical image or file here'}
                </p>
                <p className="mt-1 text-[0.82rem] text-on-surface/40">
                  Prescriptions, symptom photos, and lab reports auto-route through one workflow
                </p>
              </div>
              <input
                ref={fileInputRef}
                type="file"
                className="hidden"
                accept="image/*,.pdf"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) void handleFileSelect(file);
                }}
              />
            </div>

            {previewUrl ? (
              <div className="overflow-hidden rounded-3xl border border-outline-variant/30 bg-surface-container-low">
                <img src={previewUrl} alt="Uploaded medical context" className="h-64 w-full object-contain bg-surface" />
                <div className="px-5 py-3 text-sm text-on-surface/60">
                  <p className="font-medium text-on-surface/80">{selectedFile?.name}</p>
                  <p>{selectedFile ? `${(selectedFile.size / 1024).toFixed(1)} KB` : ''}</p>
                </div>
              </div>
            ) : null}
          </div>

          <div className="space-y-4">
            {analyzing ? (
              <div className="flex flex-col items-center justify-center gap-4 rounded-[1.75rem] bg-surface-container-low px-6 py-16">
                <Loader2 className="h-10 w-10 animate-spin text-primary" />
                <p className="text-sm font-medium text-on-surface/65">Running the unified vision workflow...</p>
                <div className="flex flex-wrap justify-center gap-2">
                  <Pill>Drive save</Pill>
                  <Pill tone="sand">Auto classification</Pill>
                  <Pill tone="sage">Snapshot</Pill>
                </div>
              </div>
            ) : visionResult ? (
              <div className="space-y-4">
                <div className="rounded-3xl bg-primary-fixed/25 px-5 py-5">
                  <div className="mb-3 flex items-center gap-2 text-primary">
                    <CheckCircle2 className="h-5 w-5" />
                    <p className="font-medium">Vision workflow complete</p>
                  </div>
                  <div className="mb-4 flex flex-wrap items-center gap-3">
                    <Pill tone="sage">{visionResult.category}</Pill>
                    <Pill>{visionResult.model_used}</Pill>
                    {visionResult.severity ? <Pill tone="terracotta">{visionResult.severity}</Pill> : null}
                    <Pill tone="sand">{visionResult.confidence}% confidence</Pill>
                  </div>
                  <p className="text-sm leading-7 text-on-surface/68">{visionResult.summary}</p>
                </div>

                <div className="space-y-3 rounded-3xl bg-surface-container-low px-5 py-4">
                  <p className="text-sm uppercase tracking-[0.18em] text-secondary/70">Workflow output</p>
                  <p className="text-sm leading-7 text-on-surface/68">
                    Saved to Drive as{' '}
                    <span className="font-medium text-on-surface/80">{visionResult.drive_upload.file_name}</span>.
                  </p>
                  {visionResult.prescription_id ? (
                    <p className="text-sm leading-7 text-on-surface/68">Prescription record created: #{visionResult.prescription_id}</p>
                  ) : null}
                  {visionResult.snapshot_id ? (
                    <p className="text-sm leading-7 text-on-surface/68">History snapshot created: #{visionResult.snapshot_id}</p>
                  ) : null}
                  {visionResult.findings.map((finding) => (
                    <div key={finding} className="flex items-start gap-3">
                      <span className="mt-1 h-2 w-2 shrink-0 rounded-full bg-secondary" />
                      <p className="text-sm leading-7 text-on-surface/68">{finding}</p>
                    </div>
                  ))}
                </div>

                <div className="flex flex-wrap gap-3">
                  <button
                    onClick={askFollowUp}
                    className="river-stone-btn bg-surface-container-low px-5 py-3 text-on-surface/80"
                  >
                    {busyAction === 'followup' ? 'Preparing...' : 'Ask follow-up'}
                  </button>
                  <button
                    onClick={createDoctorHandoff}
                    disabled={isBusy}
                    className={`river-stone-btn bg-secondary-container px-5 py-3 text-on-secondary-container ${disabledButtonClass}`}
                  >
                    {busyAction === 'escalate' ? 'Sending...' : 'Send doctor handoff'}
                  </button>
                  <button
                    onClick={chatWithDoctor}
                    className="river-stone-btn bg-primary-fixed/40 px-5 py-3 text-primary"
                  >
                    {busyAction === 'doctor-chat' ? 'Preparing...' : 'Chat with doctor'}
                  </button>
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center gap-3 rounded-[1.75rem] bg-surface-container-low px-6 py-16 text-center">
                <Sparkles className="h-10 w-10 text-on-surface/25" />
                <p className="text-sm font-medium text-on-surface/55">Upload once to trigger the full vision workflow</p>
                <p className="max-w-xs text-xs text-on-surface/40">
                  The backend now auto-detects the document type, saves to Drive, extracts prescriptions when present, and stores a history snapshot.
                </p>
              </div>
            )}
          </div>
        </div>

        <div className="flex flex-wrap gap-3 pt-4">
          <button
            onClick={scheduleFollowUp}
            disabled={isBusy}
            className={`river-stone-btn bg-surface-container-low px-6 py-4 text-on-surface/75 hover:bg-surface-container-high ${disabledButtonClass}`}
          >
            {busyAction === 'calendar' ? 'Scheduling...' : 'Create follow-up'}
          </button>
          <button
            onClick={createDoctorHandoff}
            disabled={isBusy}
            className={`river-stone-btn bg-secondary-container px-6 py-4 text-on-secondary-container ${disabledButtonClass}`}
          >
            {busyAction === 'escalate' ? 'Sending...' : 'Send doctor handoff'}
          </button>
        </div>
      </SoftCard>

          {supportResult ? (
            <SoftCard>
              <div className="flex items-center gap-3 text-secondary">
                <Waves className="h-5 w-5" />
                <h3 className="font-serif text-2xl">Generated Video Placeholder</h3>
              </div>
              {supportResult.diet_plan ? (
                <>
                  <p className="mt-3 text-sm leading-7 text-on-surface/65">{supportResult.diet_plan.plan_summary}</p>
                  <div className="mt-5 space-y-3">
                    {supportResult.diet_plan.meal_rules?.map((rule) => (
                      <div key={rule} className="rounded-[1.4rem] bg-surface-container-low px-4 py-3 text-sm leading-7 text-on-surface/70">
                        {rule}
                      </div>
                    ))}
                  </div>
                </>
              ) : (
                <p className="mt-3 text-sm leading-7 text-on-surface/65">No specific dietary guidance linked with this medication route.</p>
              )}
            </SoftCard>
          ) : null}
    </motion.div>
  );
}
