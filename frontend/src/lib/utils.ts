import { clsx, type ClassValue } from "clsx";

/** Join class names, filtering out falsy values. */
export function cn(...classes: ClassValue[]): string {
  return clsx(classes);
}
