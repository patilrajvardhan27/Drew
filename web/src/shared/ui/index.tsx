import type { ButtonHTMLAttributes, CSSProperties, ReactNode } from "react";
import "./ui.css";

type Variant = "primary" | "outline" | "quiet";

export function Button({
  variant = "primary",
  className = "",
  type = "button",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant }) {
  return <button type={type} className={`button button-${variant} ${className}`} {...props} />;
}

export function Tag({ children }: { children: ReactNode }) {
  return <span className="tag">{children}</span>;
}

export function Skeleton({ width = "100%", height = 16, style }: { width?: string | number; height?: number; style?: CSSProperties }) {
  return <span aria-hidden="true" className="skeleton" style={{ width, height, ...style }} />;
}

export function SkeletonSheet({ lines = 5 }: { lines?: number }) {
  return (
    <div className="sheet" aria-busy="true" aria-label="Loading">
      <Skeleton width="40%" height={28} style={{ marginBottom: 20 }} />
      {Array.from({ length: lines }, (_, i) => (
        <Skeleton key={i} width={`${92 - (i % 3) * 14}%`} style={{ marginBottom: 12 }} />
      ))}
    </div>
  );
}

export function PageSheet({
  label,
  actions,
  children,
  innerRef,
}: {
  label: string;
  actions?: ReactNode;
  children: ReactNode;
  innerRef?: (node: HTMLElement | null) => void;
}) {
  return (
    <section className="sheet" ref={innerRef} aria-label={label}>
      <header className="sheet-head">
        <span className="sheet-label">{label}</span>
        {actions}
      </header>
      {children}
    </section>
  );
}

export function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="field">
      <span>{label}</span>
      {children}
    </label>
  );
}
