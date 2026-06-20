import * as React from "react";

export type SearchBarProps = React.InputHTMLAttributes<HTMLInputElement>;

/**
 * The full-width search input used on `/features` and `/commands` (the
 * client-side filter box). Visual only here — the live site layers the filter
 * script on top. Mirrors the `<input type="search">` in those templates.
 */
export function SearchBar({
  placeholder = "Search…",
  className = "",
  ...props
}: SearchBarProps) {
  return (
    <input
      type="search"
      autoComplete="off"
      placeholder={placeholder}
      className={`w-full rounded-lg border border-slate-700 bg-slate-900 px-4 py-2.5 text-sm placeholder-slate-500 focus:border-sky-500 focus:outline-none ${className}`}
      {...props}
    />
  );
}
