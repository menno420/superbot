import * as React from "react";

import { buttonClasses, type ButtonVariant } from "./Button";

export interface ButtonLinkProps
  extends React.AnchorHTMLAttributes<HTMLAnchorElement> {
  /** Visual style — matches {@link Button}. */
  variant?: ButtonVariant;
}

/**
 * An anchor styled as a brand button. The live site renders its calls-to-action
 * ("Add to Discord", "Explore features") as links, not `<button>`s, so this is
 * the faithful element for navigation/action CTAs. Shares {@link Button}'s
 * styling via `buttonClasses`.
 */
export function ButtonLink({
  variant = "primary",
  className = "",
  ...props
}: ButtonLinkProps) {
  return (
    <a className={`inline-block ${buttonClasses(variant)} ${className}`} {...props} />
  );
}
