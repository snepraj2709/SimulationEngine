import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";

const urlSchema = z.object({
  url: z.string().url("Enter a valid company or product URL."),
});

type URLFormValues = z.infer<typeof urlSchema>;

interface URLSubmitFormProps {
  isLoading?: boolean;
  onSubmit: (values: URLFormValues) => Promise<void> | void;
}

export function URLSubmitForm({ isLoading = false, onSubmit }: URLSubmitFormProps) {
  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<URLFormValues>({
    resolver: zodResolver(urlSchema),
    defaultValues: { url: "https://www.netflix.com/" },
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="panel p-6">
      <div className="flex flex-col gap-4">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.16em] text-slate-500">URL Intake</p>
          <h2 className="mt-2 text-2xl font-semibold text-slate-950">Turn a product URL into a decision simulation.</h2>
          <p className="mt-2 max-w-2xl text-sm text-slate-600">
            The engine extracts product signals, generates ICPs, suggests scenarios, and simulates retention, downgrade, churn, revenue, and sentiment shifts.
          </p>
        </div>
        <label className="flex flex-col gap-2">
          <span className="text-sm font-medium text-slate-700">Company or product URL</span>
          <div className="flex flex-col gap-3 md:flex-row">
            <input
              {...register("url")}
              placeholder="https://www.example.com/"
              className="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-slate-500"
            />
            <button
              type="submit"
              disabled={isLoading}
              className="rounded-2xl bg-slate-950 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
            >
              {isLoading ? "Analyzing..." : "Analyze URL"}
            </button>
          </div>
          {errors.url ? <span className="text-sm text-red-600">{errors.url.message}</span> : null}
        </label>
        <div className="flex flex-wrap items-center gap-3 text-sm">
          <button
            type="button"
            onClick={() => setValue("url", "https://www.netflix.com/")}
            className="rounded-full border border-slate-300 px-3 py-1.5 font-medium text-slate-700 hover:border-slate-400 hover:bg-slate-100"
          >
            Load Netflix demo
          </button>
          <span className="text-slate-500">Includes a seeded “premium price increase in India” default scenario.</span>
        </div>
      </div>
    </form>
  );
}
