import { useEffect, useState } from 'react';
import { motion } from 'motion/react';
import { HeartPulse, Save, ShieldPlus, UserRound } from 'lucide-react';
import {
  addPatientVital,
  fetchPatientProfile,
  fetchPatientVitals,
  patient2Image,
  updatePatientProfile,
  type PatientProfile,
  type PatientVital,
  type WorkspacePayload,
} from '../lib/api';
import { ErrorState, LoadingState } from '../components/States';

type ProfileFormState = {
  full_name: string;
  preferred_language: string;
  date_of_birth: string;
  summary: string;
  height_cm: string;
  weight_kg: string;
  blood_group: string;
  allergies: string;
  emergency_contact_name: string;
  emergency_contact_phone: string;
  primary_language: string;
  notes: string;
};

type VitalFormState = {
  blood_pressure: string;
  heart_rate_bpm: string;
  blood_glucose_mg_dl: string;
  temperature_c: string;
  weight_kg: string;
};

const emptyVitalForm: VitalFormState = {
  blood_pressure: '',
  heart_rate_bpm: '',
  blood_glucose_mg_dl: '',
  temperature_c: '',
  weight_kg: '',
};

function assertPositive(value: number | null, message: string) {
  if (value !== null && value <= 0) {
    throw new Error(message);
  }
}

function assertHumanTemperature(value: number | null) {
  if (value !== null && (value < 30 || value > 45)) {
    throw new Error('Temperature out of range');
  }
}

function profileToForm(profile: PatientProfile): ProfileFormState {
  return {
    full_name: profile.full_name ?? '',
    preferred_language: profile.preferred_language ?? '',
    date_of_birth: profile.date_of_birth ?? '',
    summary: profile.summary ?? '',
    height_cm: profile.height_cm == null ? '' : String(profile.height_cm),
    weight_kg: profile.weight_kg == null ? '' : String(profile.weight_kg),
    blood_group: profile.blood_group ?? '',
    allergies: profile.allergies.join(', '),
    emergency_contact_name: profile.emergency_contact_name ?? '',
    emergency_contact_phone: profile.emergency_contact_phone ?? '',
    primary_language: profile.primary_language ?? '',
    notes: profile.notes ?? '',
  };
}

export function Profile({
  workspace,
  loading,
  error,
  onRefresh,
  patientId,
}: {
  workspace: WorkspacePayload | null;
  loading: boolean;
  error: string | null;
  onRefresh: () => void;
  patientId: number;
}) {
  const [profile, setProfile] = useState<PatientProfile | null>(workspace?.profile ?? null);
  const [form, setForm] = useState<ProfileFormState | null>(workspace?.profile ? profileToForm(workspace.profile) : null);
  const [vitals, setVitals] = useState<PatientVital[]>(workspace?.vitals ?? []);
  const [vitalForm, setVitalForm] = useState<VitalFormState>(emptyVitalForm);
  const [screenLoading, setScreenLoading] = useState(!workspace);
  const [screenError, setScreenError] = useState<string | null>(null);
  const [saveState, setSaveState] = useState<'idle' | 'saving' | 'saved'>('idle');
  const [vitalState, setVitalState] = useState<'idle' | 'saving' | 'saved'>('idle');
  const [formErrors, setFormErrors] = useState<Partial<Record<keyof ProfileFormState, string>>>({});
  const [vitalErrors, setVitalErrors] = useState<Partial<Record<keyof VitalFormState, string>>>({});

  useEffect(() => {
    if (workspace?.patient.id !== patientId) return;

    if (workspace?.profile && !profile) {
      setProfile(workspace.profile);
      setForm(profileToForm(workspace.profile));
    }
    if (workspace?.vitals) {
      setVitals(workspace.vitals);
    }
  }, [workspace, profile, patientId]);

  useEffect(() => {
    let active = true;

    setProfile(null);
    setForm(null);
    setVitals([]);
    setScreenError(null);
    setScreenLoading(true);

    const load = async () => {
      try {
        const [profileResult, vitalsResult] = await Promise.all([
          fetchPatientProfile(patientId),
          fetchPatientVitals(patientId),
        ]);
        if (!active) return;
        setProfile(profileResult);
        setForm(profileToForm(profileResult));
        setVitals(vitalsResult);
      } catch (loadError) {
        if (!active) return;
        setScreenError(loadError instanceof Error ? loadError.message : 'Unable to load profile.');
      } finally {
        if (active) setScreenLoading(false);
      }
    };

    void load();

    return () => {
      active = false;
    };
  }, [patientId]);

  if ((loading || screenLoading) && !form) return <LoadingState />;
  if ((error || screenError) && !form) return <ErrorState message={screenError || error || 'Unable to load profile.'} onRetry={onRefresh} />;
  if (!form || !profile) return <ErrorState message="Profile data is not available yet." onRetry={onRefresh} />;

  const handleChange = (field: keyof ProfileFormState, value: string) => {
    setForm((current) => (current ? { ...current, [field]: value } : current));
    setFormErrors((prev) => ({ ...prev, [field]: undefined }));
    setSaveState('idle');
  };

  const handleVitalChange = (field: keyof VitalFormState, value: string) => {
    setVitalForm((current) => ({ ...current, [field]: value }));
    setVitalErrors((prev) => ({ ...prev, [field]: undefined }));
    setVitalState('idle');
  };

  const handleSaveProfile = async () => {
    try {
      setSaveState('saving');
      setFormErrors({});
      const newErrors: Partial<Record<keyof ProfileFormState, string>> = {};
      
      const parsedHeight = form.height_cm ? parseFloat(form.height_cm) : null;
      const parsedWeight = form.weight_kg ? parseFloat(form.weight_kg) : null;
      
      if (form.height_cm && !Number.isFinite(parsedHeight)) {
        newErrors.height_cm = 'Please enter a valid height';
      }
      if (form.weight_kg && !Number.isFinite(parsedWeight)) {
        newErrors.weight_kg = 'Please enter a valid weight';
      }

      if (Object.keys(newErrors).length > 0) {
        setFormErrors(newErrors);
        throw new Error(Object.values(newErrors)[0] ?? 'Invalid profile values');
      }

      assertPositive(parsedHeight, 'Height must be > 0');
      assertPositive(parsedWeight, 'Weight must be > 0');

      const updated = await updatePatientProfile(patientId, {
        full_name: form.full_name || null,
        preferred_language: form.preferred_language || null,
        date_of_birth: form.date_of_birth || null,
        summary: form.summary || null,
        height_cm: parsedHeight,
        weight_kg: parsedWeight,
        blood_group: form.blood_group || null,
        allergies: form.allergies
          .split(',')
          .map((item) => item.trim())
          .filter(Boolean),
        emergency_contact_name: form.emergency_contact_name || null,
        emergency_contact_phone: form.emergency_contact_phone || null,
        primary_language: form.primary_language || null,
        notes: form.notes || null,
      });
      setProfile(updated);
      setForm(profileToForm(updated));
      setSaveState('saved');
      await onRefresh();
    } catch (saveError) {
      setScreenError(saveError instanceof Error ? saveError.message : 'Unable to save profile.');
      setSaveState('idle');
    }
  };

  const handleAddVital = async () => {
    try {
      setVitalState('saving');
      setVitalErrors({});
      const newErrors: Partial<Record<keyof VitalFormState, string>> = {};
      
      const parsedHeartRate = vitalForm.heart_rate_bpm ? parseFloat(vitalForm.heart_rate_bpm) : null;
      const parsedGlucose = vitalForm.blood_glucose_mg_dl ? parseFloat(vitalForm.blood_glucose_mg_dl) : null;
      const parsedTemp = vitalForm.temperature_c ? parseFloat(vitalForm.temperature_c) : null;
      const parsedWeight = vitalForm.weight_kg ? parseFloat(vitalForm.weight_kg) : null;

      if (vitalForm.heart_rate_bpm && !Number.isFinite(parsedHeartRate)) {
        newErrors.heart_rate_bpm = 'Invalid heart rate';
      }
      if (vitalForm.blood_glucose_mg_dl && !Number.isFinite(parsedGlucose)) {
        newErrors.blood_glucose_mg_dl = 'Invalid glucose';
      }
      if (vitalForm.temperature_c && !Number.isFinite(parsedTemp)) {
        newErrors.temperature_c = 'Invalid temperature';
      }
      if (vitalForm.weight_kg && !Number.isFinite(parsedWeight)) {
        newErrors.weight_kg = 'Invalid weight';
      }

      if (Object.keys(newErrors).length > 0) {
        setVitalErrors(newErrors);
        throw new Error(Object.values(newErrors)[0] ?? 'Invalid vital values');
      }

      assertPositive(parsedHeartRate, 'Heart rate must be > 0');
      assertPositive(parsedGlucose, 'Glucose must be > 0');
      assertHumanTemperature(parsedTemp);
      assertPositive(parsedWeight, 'Weight must be > 0');

      const created = await addPatientVital(patientId, {
        blood_pressure: vitalForm.blood_pressure || null,
        heart_rate_bpm: parsedHeartRate,
        blood_glucose_mg_dl: parsedGlucose,
        temperature_c: parsedTemp,
        weight_kg: parsedWeight,
        source: 'manual_entry',
      });
      setVitals((current) => [created, ...current]);
      setVitalForm(emptyVitalForm);
      setVitalState('saved');
      await onRefresh();
    } catch (saveError) {
      setScreenError(saveError instanceof Error ? saveError.message : 'Unable to save vitals.');
      setVitalState('idle');
    }
  };

  return (
    <motion.div initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -18 }} className="space-y-8 pb-12">
      <section className="glass-panel relative overflow-hidden rounded-[1.5rem] p-8">
        <div className="absolute right-[-2rem] top-[-2rem] h-40 w-40 rounded-full bg-primary-fixed/25 blur-3xl" />
        <div className="relative z-10 flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex items-center gap-5">
            <div className="h-24 w-24 overflow-hidden rounded-[2rem] border-4 border-surface-container-lowest/60 shadow-lg">
              <img src={patient2Image} alt={profile.full_name} className="h-full w-full object-cover" />
            </div>
            <div>
              <p className="eyebrow text-primary/70">Profile</p>
              <h1 className="mt-3 font-serif text-[2.2rem] leading-tight text-on-surface">{profile.full_name}</h1>
              <p className="mt-2 text-sm text-on-surface/55">
                {profile.primary_language || profile.preferred_language || 'English'} • Blood group {profile.blood_group || 'Not set'}
              </p>
            </div>
          </div>

          <div className="grid gap-3 sm:grid-cols-3">
            <div className="rounded-[1.1rem] bg-surface-container-lowest/45 px-5 py-4 glass-edge">
              <p className="eyebrow text-on-surface/45">Height</p>
              <p className="mt-2 font-serif text-2xl">{profile.height_cm ? `${profile.height_cm} cm` : '--'}</p>
            </div>
            <div className="rounded-[1.1rem] bg-surface-container-lowest/45 px-5 py-4 glass-edge">
              <p className="eyebrow text-on-surface/45">Weight</p>
              <p className="mt-2 font-serif text-2xl">{profile.weight_kg ? `${profile.weight_kg} kg` : '--'}</p>
            </div>
            <div className="rounded-[1.1rem] bg-surface-container-lowest/45 px-5 py-4 glass-edge">
              <p className="eyebrow text-on-surface/45">Updated</p>
              <p className="mt-2 font-serif text-xl">{profile.updated_at ? new Date(profile.updated_at).toLocaleDateString() : 'New'}</p>
            </div>
          </div>
        </div>
      </section>

      {screenError ? <ErrorState message={screenError} onRetry={onRefresh} /> : null}

      <section className="grid gap-6 xl:grid-cols-[1.25fr_0.75fr]">
        <div className="glass-panel rounded-[1.5rem] p-8">
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="eyebrow text-primary/70">Care identity</p>
              <h2 className="mt-3 font-serif text-[1.8rem] text-on-surface">Editable patient profile</h2>
            </div>
            <button
              onClick={handleSaveProfile}
              className="river-stone-btn flex items-center gap-2 bg-primary px-5 py-3 text-surface"
              disabled={saveState === 'saving'}
            >
              <Save className="h-4 w-4" />
              <span>{saveState === 'saving' ? 'Saving...' : saveState === 'saved' ? 'Saved' : 'Save profile'}</span>
            </button>
          </div>

          <div className="mt-8 grid gap-5 md:grid-cols-2">
            <label className="space-y-2">
              <span className="text-sm text-on-surface/60">Full name</span>
              <input value={form.full_name} onChange={(event) => handleChange('full_name', event.target.value)} className="input-shell w-full" />
            </label>
            <label className="space-y-2">
              <span className="text-sm text-on-surface/60">Date of birth</span>
              <input type="date" value={form.date_of_birth} onChange={(event) => handleChange('date_of_birth', event.target.value)} className="input-shell w-full" />
            </label>
            <label className="space-y-2">
              <span className="text-sm text-on-surface/60">Preferred language</span>
              <input value={form.preferred_language} onChange={(event) => handleChange('preferred_language', event.target.value)} className="input-shell w-full" />
            </label>
            <label className="space-y-2">
              <span className="text-sm text-on-surface/60">Primary language</span>
              <input value={form.primary_language} onChange={(event) => handleChange('primary_language', event.target.value)} className="input-shell w-full" />
            </label>
            <label className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm text-on-surface/60">Height (cm)</span>
                {formErrors.height_cm && <span className="text-xs text-secondary">{formErrors.height_cm}</span>}
              </div>
              <input type="number" step="any" value={form.height_cm} onChange={(event) => handleChange('height_cm', event.target.value)} className={`input-shell w-full ${formErrors.height_cm ? 'border-secondary/50 focus:border-secondary' : ''}`} inputMode="decimal" />
            </label>
            <label className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm text-on-surface/60">Weight (kg)</span>
                {formErrors.weight_kg && <span className="text-xs text-secondary">{formErrors.weight_kg}</span>}
              </div>
              <input type="number" step="any" value={form.weight_kg} onChange={(event) => handleChange('weight_kg', event.target.value)} className={`input-shell w-full ${formErrors.weight_kg ? 'border-secondary/50 focus:border-secondary' : ''}`} inputMode="decimal" />
            </label>
            <label className="space-y-2">
              <span className="text-sm text-on-surface/60">Blood group</span>
              <input value={form.blood_group} onChange={(event) => handleChange('blood_group', event.target.value)} className="input-shell w-full" />
            </label>
            <label className="space-y-2">
              <span className="text-sm text-on-surface/60">Allergies</span>
              <input value={form.allergies} onChange={(event) => handleChange('allergies', event.target.value)} className="input-shell w-full" placeholder="Peanuts, penicillin" />
            </label>
            <label className="space-y-2">
              <span className="text-sm text-on-surface/60">Emergency contact</span>
              <input value={form.emergency_contact_name} onChange={(event) => handleChange('emergency_contact_name', event.target.value)} className="input-shell w-full" />
            </label>
            <label className="space-y-2">
              <span className="text-sm text-on-surface/60">Emergency phone</span>
              <input value={form.emergency_contact_phone} onChange={(event) => handleChange('emergency_contact_phone', event.target.value)} className="input-shell w-full" />
            </label>
            <label className="space-y-2 md:col-span-2">
              <span className="text-sm text-on-surface/60">Clinical summary</span>
              <textarea value={form.summary} onChange={(event) => handleChange('summary', event.target.value)} className="input-shell min-h-28 w-full resize-y" />
            </label>
            <label className="space-y-2 md:col-span-2">
              <span className="text-sm text-on-surface/60">Care notes</span>
              <textarea value={form.notes} onChange={(event) => handleChange('notes', event.target.value)} className="input-shell min-h-28 w-full resize-y" />
            </label>
          </div>
        </div>

        <div className="space-y-6">
          <div className="glass-panel rounded-[1.5rem] p-8">
            <div className="flex items-center gap-3">
              <div className="rounded-2xl bg-primary-fixed/30 p-3 text-primary">
                <ShieldPlus className="h-5 w-5" />
              </div>
              <div>
                <p className="eyebrow text-primary/70">Safety card</p>
                <h3 className="mt-2 font-serif text-xl">Emergency anchors</h3>
              </div>
            </div>
            <div className="mt-6 space-y-4 text-sm text-on-surface/70">
              <div className="rounded-[1rem] bg-surface-container-lowest/45 p-4 glass-edge">
                <p className="text-on-surface/45">Emergency contact</p>
                <p className="mt-2 font-medium text-on-surface">{profile.emergency_contact_name || 'Not added yet'}</p>
                <p className="text-on-surface/60">{profile.emergency_contact_phone || 'No phone saved'}</p>
              </div>
              <div className="rounded-[1rem] bg-surface-container-lowest/45 p-4 glass-edge">
                <p className="text-on-surface/45">Allergy ledger</p>
                <p className="mt-2 font-medium text-on-surface">{profile.allergies.length ? profile.allergies.join(', ') : 'No allergies recorded'}</p>
              </div>
            </div>
          </div>

          <div className="glass-panel rounded-[1.5rem] p-8">
            <div className="flex items-center gap-3">
              <div className="rounded-2xl bg-secondary-container/30 p-3 text-secondary">
                <UserRound className="h-5 w-5" />
              </div>
              <div>
                <p className="eyebrow text-secondary/80">Snapshot note</p>
                <h3 className="mt-2 font-serif text-xl">Profile saves create a condition snapshot</h3>
              </div>
            </div>
            <p className="mt-5 text-sm leading-7 text-on-surface/65">
              Each profile update now captures the current profile, condition list, prescription context, and latest vitals so the doctor workspace can look back at state changes later.
            </p>
          </div>
        </div>
      </section>

      <section className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <div className="glass-panel rounded-[1.5rem] p-8">
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="eyebrow text-primary/70">Vitals intake</p>
              <h2 className="mt-3 font-serif text-[1.8rem] text-on-surface">Record today’s metrics</h2>
            </div>
            <button
              onClick={handleAddVital}
              className="river-stone-btn flex items-center gap-2 bg-secondary-container px-5 py-3 text-on-secondary-container"
              disabled={vitalState === 'saving'}
            >
              <HeartPulse className="h-4 w-4" />
              <span>{vitalState === 'saving' ? 'Saving...' : vitalState === 'saved' ? 'Saved' : 'Add vital'}</span>
            </button>
          </div>

          <div className="mt-8 grid gap-5 md:grid-cols-2">
            <label className="space-y-2">
              <span className="text-sm text-on-surface/60">Blood pressure</span>
              <input value={vitalForm.blood_pressure} onChange={(event) => handleVitalChange('blood_pressure', event.target.value)} className="input-shell w-full" placeholder="120/80" />
            </label>
            <label className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm text-on-surface/60">Heart rate (bpm)</span>
                {vitalErrors.heart_rate_bpm && <span className="text-xs text-secondary">{vitalErrors.heart_rate_bpm}</span>}
              </div>
              <input type="number" step="any" value={vitalForm.heart_rate_bpm} onChange={(event) => handleVitalChange('heart_rate_bpm', event.target.value)} className={`input-shell w-full ${vitalErrors.heart_rate_bpm ? 'border-secondary/50 focus:border-secondary' : ''}`} inputMode="numeric" />
            </label>
            <label className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm text-on-surface/60">Blood glucose (mg/dL)</span>
                {vitalErrors.blood_glucose_mg_dl && <span className="text-xs text-secondary">{vitalErrors.blood_glucose_mg_dl}</span>}
              </div>
              <input type="number" step="any" value={vitalForm.blood_glucose_mg_dl} onChange={(event) => handleVitalChange('blood_glucose_mg_dl', event.target.value)} className={`input-shell w-full ${vitalErrors.blood_glucose_mg_dl ? 'border-secondary/50 focus:border-secondary' : ''}`} inputMode="decimal" />
            </label>
            <label className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm text-on-surface/60">Temperature (C)</span>
                {vitalErrors.temperature_c && <span className="text-xs text-secondary">{vitalErrors.temperature_c}</span>}
              </div>
              <input type="number" step="any" value={vitalForm.temperature_c} onChange={(event) => handleVitalChange('temperature_c', event.target.value)} className={`input-shell w-full ${vitalErrors.temperature_c ? 'border-secondary/50 focus:border-secondary' : ''}`} inputMode="decimal" />
            </label>
            <label className="space-y-2 md:col-span-2">
              <div className="flex justify-between items-center">
                <span className="text-sm text-on-surface/60">Weight (kg)</span>
                {vitalErrors.weight_kg && <span className="text-xs text-secondary">{vitalErrors.weight_kg}</span>}
              </div>
              <input type="number" step="any" value={vitalForm.weight_kg} onChange={(event) => handleVitalChange('weight_kg', event.target.value)} className={`input-shell w-full ${vitalErrors.weight_kg ? 'border-secondary/50 focus:border-secondary' : ''}`} inputMode="decimal" />
            </label>
          </div>
        </div>

        <div className="glass-panel rounded-[1.5rem] p-8">
          <p className="eyebrow text-primary/70">Recent vitals</p>
          <h2 className="mt-3 font-serif text-[1.8rem] text-on-surface">Trend-ready entries</h2>

          <div className="mt-8 space-y-4">
            {vitals.length === 0 ? (
              <div className="rounded-[1.25rem] bg-surface-container-lowest/35 p-6 text-sm text-on-surface/55 glass-edge">
                No vitals recorded yet. Add the first entry from the form to start building the timeline.
              </div>
            ) : (
              vitals.slice(0, 6).map((vital) => (
                <div key={vital.id} className="rounded-[1.25rem] bg-surface-container-lowest/35 p-5 glass-edge">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <p className="font-serif text-lg">
                      {new Date(vital.recorded_at).toLocaleDateString()} • {new Date(vital.recorded_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </p>
                    <span className="text-xs uppercase tracking-[0.2em] text-on-surface/45">{vital.source || 'manual'}</span>
                  </div>
                  <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                    <div><p className="text-xs text-on-surface/45">Blood pressure</p><p className="mt-1 font-medium">{vital.blood_pressure || '--'}</p></div>
                    <div><p className="text-xs text-on-surface/45">Heart rate</p><p className="mt-1 font-medium">{vital.heart_rate_bpm ? `${vital.heart_rate_bpm} bpm` : '--'}</p></div>
                    <div><p className="text-xs text-on-surface/45">Glucose</p><p className="mt-1 font-medium">{vital.blood_glucose_mg_dl ? `${vital.blood_glucose_mg_dl} mg/dL` : '--'}</p></div>
                    <div><p className="text-xs text-on-surface/45">Temperature</p><p className="mt-1 font-medium">{vital.temperature_c ? `${vital.temperature_c} C` : '--'}</p></div>
                    <div><p className="text-xs text-on-surface/45">Weight</p><p className="mt-1 font-medium">{vital.weight_kg ? `${vital.weight_kg} kg` : '--'}</p></div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </section>
    </motion.div>
  );
}
