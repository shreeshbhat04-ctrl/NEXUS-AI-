import React from 'react';
import { Brain, Loader2, Mail, Phone, Stethoscope } from 'lucide-react';
import { Pill } from './ui';

interface DoctorProfile {
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
}

interface DoctorCardProps {
  doctor: DoctorProfile;
  isSelected: boolean;
  hasBrief: boolean;
  isLoading: boolean;
  onSelect: (id: string) => void;
  onGenerate: (id: string) => void;
}

export const DoctorCard: React.FC<DoctorCardProps> = ({
  doctor,
  isSelected,
  hasBrief,
  isLoading,
  onSelect,
  onGenerate,
}) => {
  return (
    <article
      className={`group relative flex h-full flex-col gap-6 rounded-[2rem] border p-7 transition-all duration-500 overflow-hidden ${
        isSelected
          ? 'border-primary/40 bg-surface-container-lowest shadow-[0_20px_50px_-12px_rgba(60,64,67,0.1)] ring-1 ring-primary/10'
          : 'border-outline-variant/10 bg-surface-container-lowest/50 shadow-sm hover:border-outline-variant/30 hover:shadow-md'
      }`}
    >
      {/* Decorative gradient blur */}
      {isSelected && (
        <div className="absolute -right-10 -top-10 h-32 w-32 rounded-full bg-primary/5 blur-[40px] transition-opacity group-hover:opacity-100" />
      )}

      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-5">
          <div className="relative">
            <div className={`h-24 w-24 overflow-hidden rounded-2xl border-2 p-1 transition-all duration-500 ${
              isSelected ? 'border-primary scale-105 rotate-1 shadow-lg' : 'border-surface-container-high'
            }`}>
              <img src={doctor.image} alt={doctor.name} className="h-full w-full rounded-xl object-cover" />
            </div>
            {isSelected && (
              <div className="absolute -bottom-2 -right-2 rounded-full bg-primary p-1.5 text-on-primary shadow-sm">
                <Stethoscope className="h-4 w-4" />
              </div>
            )}
          </div>
          <div>
            <h3 className="font-serif text-[1.65rem] leading-tight tracking-tight text-on-surface">
              {doctor.name}
            </h3>
            <p className="mt-1 text-[0.75rem] font-bold uppercase tracking-[0.2em] text-primary/80">
              {doctor.specialty}
            </p>
          </div>
        </div>
        <div className="flex flex-col items-end gap-2">
          <Pill tone={hasBrief ? 'sage' : 'sand'}>
            <span className="flex items-center gap-1.5">
              {hasBrief && <span className="h-1.5 w-1.5 rounded-full bg-sage animate-pulse" />}
              {hasBrief ? 'Brief ready' : 'Ready for review'}
            </span>
          </Pill>
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <div className="rounded-2xl bg-surface-container-low/50 p-4 transition-colors group-hover:bg-surface-container-low">
          <p className="text-[0.65rem] font-bold uppercase tracking-[0.2em] text-on-surface/40">Success rate</p>
          <div className="mt-1.5 flex items-baseline gap-1">
            <p className="text-xl font-semibold text-on-surface">98</p>
            <span className="text-xs text-on-surface/40">%</span>
          </div>
        </div>
        <div className="rounded-2xl bg-surface-container-low/50 p-4 transition-colors group-hover:bg-surface-container-low">
          <p className="text-[0.65rem] font-bold uppercase tracking-[0.2em] text-on-surface/40">Total cases</p>
          <p className="mt-1.5 text-xl font-semibold text-on-surface">{doctor.casesClosed}</p>
        </div>
      </div>

      <div className="space-y-4">
        <div className="flex flex-col gap-2.5">
          <div className="flex items-center gap-3 text-on-surface/60">
            <div className="rounded-full bg-surface-container-high p-1.5">
              <Mail className="h-3.5 w-3.5" />
            </div>
            <span className="text-[0.82rem] font-medium truncate">{doctor.email}</span>
          </div>
          <div className="flex items-center gap-3 text-on-surface/60">
            <div className="rounded-full bg-surface-container-high p-1.5">
              <Phone className="h-3.5 w-3.5" />
            </div>
            <span className="text-[0.82rem] font-medium">{doctor.phone}</span>
          </div>
        </div>

        <div className="space-y-3 border-t border-outline-variant/10 pt-4">
          <p className="text-[0.65rem] font-bold uppercase tracking-[0.2em] text-on-surface/40">
            Core focus
          </p>
          <div className="flex flex-wrap gap-2">
            {doctor.trackedConditions.map((condition) => (
              <span
                key={condition}
                className="rounded-lg border border-outline-variant/10 bg-surface-container-lowest px-3 py-1.5 text-[0.7rem] font-semibold text-on-surface/70 transition-colors hover:border-primary/20 hover:text-primary"
              >
                {condition}
              </span>
            ))}
          </div>
          <p className="text-[0.88rem] leading-7 text-on-surface/60 italic font-medium">
            "{doctor.focusNote}"
          </p>
        </div>
      </div>

      <div className="mt-auto flex flex-col gap-3 pt-4">
        <div className="flex gap-3">
          <button 
            onClick={() => onSelect(doctor.id)}
            className={`flex-1 rounded-2xl px-5 py-3.5 text-sm font-semibold transition-all duration-300 ${
              isSelected
                ? 'bg-primary/10 text-primary shadow-sm'
                : 'bg-surface-container-low text-on-surface/70 hover:bg-surface-container-high'
            }`}
          >
            {isSelected ? 'Selected' : 'Use profile'}
          </button>
          <button className="rounded-2xl bg-surface-container-low p-3.5 text-on-surface/60 hover:bg-surface-container-high transition-colors">
            <Brain className="h-5 w-5" />
          </button>
        </div>
        <button
          onClick={() => onGenerate(doctor.id)}
          disabled={isLoading}
          className="relative overflow-hidden rounded-2xl bg-primary px-6 py-4 text-sm font-bold text-on-primary transition-all hover:shadow-[0_12px_30px_-8px_rgba(60,64,67,0.2)] disabled:opacity-60"
        >
          <span className="flex items-center justify-center gap-2">
            {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
            {hasBrief ? 'Update AI comprehension' : 'Generate clinical brief'}
          </span>
        </button>
      </div>
    </article>
  );
};

const Sparkles: React.FC<{ className?: string }> = ({ className }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z" />
    <path d="M5 3v4" /><path d="M3 5h4" /><path d="M21 17v4" /><path d="M19 19h4" />
  </svg>
);
