import * as React from "react";

export interface StepCardProps {
  /** The step number/marker shown in the circle. */
  number: React.ReactNode;
  /** Step title. */
  title: string;
  /** Step description. */
  body: string;
}

/**
 * A single "how it works" step — a numbered circle, a title, and a short
 * description. Mirrors the step cards in `botsite/index.html`.
 */
export function StepCard({ number, title, body }: StepCardProps) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 text-center">
      <div className="mx-auto mb-2 flex h-8 w-8 items-center justify-center rounded-full bg-indigo-600 font-bold">
        {number}
      </div>
      <div className="font-semibold">{title}</div>
      <div className="mt-1 text-sm text-slate-400">{body}</div>
    </div>
  );
}
