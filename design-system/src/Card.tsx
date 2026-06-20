import * as React from "react";

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
}

/**
 * The standard bordered surface used across the site (feature cards, stat
 * tiles, changelog entries). Composes with any content.
 */
export function Card({ className = "", children, ...props }: CardProps) {
  return (
    <div
      className={`rounded-xl border border-slate-800 bg-slate-900/40 p-5 ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}
