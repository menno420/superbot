import * as React from "react";

export interface StatusBuild {
  /** Deployed commit SHA. */
  commit?: string;
  /** Commit date. */
  committedAt?: string;
  /** Latest change subject line. */
  subject?: string;
}

export interface StatusCardProps {
  /** Deployed-build metadata. Absent ⇒ "Status unavailable". */
  build?: StatusBuild;
}

function Field({
  label,
  wide,
  children,
}: {
  label: string;
  wide?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div
      className={`rounded-lg border border-slate-800 bg-slate-950/40 p-4 ${
        wide ? "sm:col-span-2" : ""
      }`}
    >
      <dt className="text-slate-500">{label}</dt>
      <dd className="mt-1 text-slate-100">{children}</dd>
    </div>
  );
}

/**
 * The `/status` "online as of last deploy" card — an honest, build-time trust
 * signal (never a live claim): a status dot, the deployed build SHA, its date,
 * and the latest change. Mirrors `botsite/templates/status.html`.
 */
export function StatusCard({ build }: StatusCardProps) {
  const hasBuild = Boolean(build?.commit);
  return (
    <section className="rounded-xl border border-slate-800 bg-slate-900/50 p-6">
      <div className="flex items-center gap-3">
        <span
          className={`inline-block h-3 w-3 rounded-full ${
            hasBuild ? "bg-emerald-500" : "bg-slate-500"
          }`}
        />
        <span className="text-lg font-semibold">
          {hasBuild ? "Online as of the last deploy" : "Status unavailable"}
        </span>
      </div>
      {hasBuild ? (
        <>
          <dl className="mt-5 grid grid-cols-1 gap-4 text-sm sm:grid-cols-2">
            <Field label="Build">
              <span className="font-mono">{build?.commit}</span>
            </Field>
            {build?.committedAt ? (
              <Field label="Deployed build date">
                <time dateTime={build.committedAt}>{build.committedAt}</time>
              </Field>
            ) : null}
            {build?.subject ? (
              <Field label="Latest change" wide>
                <span className="text-slate-200">{build.subject}</span>
              </Field>
            ) : null}
          </dl>
          <p className="mt-4 text-xs text-slate-500">
            Build identifiers are public (they match the open-source repository).
            This is a generated snapshot — for a live health check we'd label it
            "live".
          </p>
        </>
      ) : (
        <p className="mt-4 text-sm text-slate-400">
          Build information isn't available right now. Please check back shortly.
        </p>
      )}
    </section>
  );
}
