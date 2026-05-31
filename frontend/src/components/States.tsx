import { RefreshCw, Sparkles, TriangleAlert } from 'lucide-react';

export function LoadingState() {
  return (
    <div className="nurture-card flex h-full min-h-[clamp(22rem,60vh,40rem)] w-full flex-col items-center justify-center gap-8 text-center">
      <div className="flex h-14 w-14 items-center justify-center rounded-full bg-primary-fixed/40 text-primary">
        <RefreshCw className="h-6 w-6 animate-spin" />
      </div>
      <div>
        <h2 className="font-serif text-2xl text-primary">Settling the room</h2>
        <p className="max-w-md text-sm leading-7 text-on-surface/60">
          nexus_ai is gathering your routines, medication signals, and care coordination details.
        </p>
      </div>
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="nurture-card flex h-full min-h-[clamp(22rem,60vh,40rem)] w-full flex-col items-center justify-center gap-8 text-center">
      <div className="flex h-14 w-14 items-center justify-center rounded-full bg-secondary-container/35 text-secondary">
        <TriangleAlert className="h-6 w-6" />
      </div>
      <div>
        <h2 className="font-serif text-2xl text-secondary">The sanctuary lost its connection</h2>
        <p className="max-w-lg text-sm leading-7 text-on-surface/65">{message}</p>
      </div>
      {onRetry ? (
        <button onClick={onRetry} className="river-stone-btn bg-secondary-container px-6 py-3 text-on-secondary-container">
          Try again
        </button>
      ) : null}
    </div>
  );
}

export function EmptyState({ title, description }: { title: string; description: string }) {
  return (
    <div className="nurture-card flex h-full min-h-[clamp(18rem,48vh,32rem)] w-full flex-col items-center justify-center gap-8 text-center">
      <div className="flex h-14 w-14 items-center justify-center rounded-full bg-tertiary-container/20 text-tertiary">
        <Sparkles className="h-6 w-6" />
      </div>
      <div>
        <h3 className="font-serif text-xl">{title}</h3>
        <p className="max-w-md text-sm leading-7 text-on-surface/60">{description}</p>
      </div>
    </div>
  );
}
