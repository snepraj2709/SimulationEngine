import clsx from "clsx";

export function cn(...values: Array<string | false | null | undefined>) {
  return clsx(values);
}

export function formatPercent(value: number) {
  return `${value.toFixed(1)}%`;
}

export function formatCurrency(value: number) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(value);
}

export function formatDate(value: string | null) {
  if (!value) return "Pending";
  return new Date(value).toLocaleString();
}
