import * as React from "react";

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  title?: string;
  description?: string;
}

export function Card({
  title,
  description,
  children,
  className = "",
  ...props
}: CardProps) {
  return (
    <div
      className={`rounded-xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-950 text-zinc-900 dark:text-zinc-100 ${className}`}
      {...props}
    >
      {title && <h3 className="text-xl font-semibold tracking-tight">{title}</h3>}
      {description && (
        <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">{description}</p>
      )}
      <div className={title || description ? "mt-4" : ""}>{children}</div>
    </div>
  );
}
