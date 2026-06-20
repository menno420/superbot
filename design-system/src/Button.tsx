import * as React from "react";

export type ButtonVariant = "primary" | "secondary";

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  /** Visual style. `primary` is the brand call-to-action (e.g. "Add to Discord"). */
  variant?: ButtonVariant;
}

const VARIANTS: Record<ButtonVariant, string> = {
  primary: "bg-indigo-600 hover:bg-indigo-500 text-white shadow",
  secondary: "border border-slate-700 hover:border-slate-500 text-slate-100",
};

/**
 * Shared class string for the brand button style. Used by both {@link Button}
 * (a real `<button>`) and `ButtonLink` (an `<a>` styled as a button — which is
 * how the live site renders its CTAs), so the look is defined in one place.
 */
export function buttonClasses(variant: ButtonVariant = "primary"): string {
  return `rounded-lg px-6 py-2.5 font-semibold transition-colors ${VARIANTS[variant]}`;
}

/**
 * The primary action button used across the site — most visibly the persistent
 * "Add to Discord" call-to-action.
 */
export function Button({
  variant = "primary",
  className = "",
  ...props
}: ButtonProps) {
  return (
    <button className={`${buttonClasses(variant)} ${className}`} {...props} />
  );
}
