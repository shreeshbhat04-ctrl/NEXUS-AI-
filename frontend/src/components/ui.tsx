import type { ReactNode } from 'react';

export function SectionShell({
  eyebrow,
  title,
  description,
  children,
  align = 'left',
}: {
  eyebrow?: string;
  title: ReactNode;
  description?: ReactNode;
  children?: ReactNode;
  align?: 'left' | 'center';
}) {
  return (
    <section className={`space-y-4 ${align === 'center' ? 'text-center' : ''}`}>
      {eyebrow ? <p className="eyebrow text-primary/75">{eyebrow}</p> : null}
      <div className="space-y-4">
        <h1 className="max-w-4xl font-serif text-[2.2rem] font-semibold leading-[1.04] tracking-[-0.03em] md:text-[2.6rem] xl:text-[3rem]">{title}</h1>
        {description ? <p className="max-w-3xl text-[1.02rem] leading-8 text-on-surface/68 xl:text-[1.08rem]">{description}</p> : null}
      </div>
      {children}
    </section>
  );
}

export function SoftCard({ children, className = '' }: { children: ReactNode; className?: string }) {
  return <div className={`nurture-card ${className}`}>{children}</div>;
}

export function Pill({ children, tone = 'sage' }: { children: ReactNode; tone?: 'sage' | 'terracotta' | 'sand' }) {
  const styles = {
    sage: 'bg-primary-fixed/45 text-primary',
    terracotta: 'bg-secondary-container/35 text-secondary',
    sand: 'bg-tertiary-container/22 text-tertiary',
  };
  return <span className={`inline-flex rounded-full px-3 py-1 text-xs font-medium ${styles[tone]}`}>{children}</span>;
}
