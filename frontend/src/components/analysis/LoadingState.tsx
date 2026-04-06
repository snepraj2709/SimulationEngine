interface LoadingStateProps {
  title: string;
  description?: string;
}

export function LoadingState({ title, description }: LoadingStateProps) {
  return (
    <div className="panel p-8">
      <div className="flex items-center gap-4">
        <div className="h-10 w-10 animate-spin rounded-full border-4 border-slate-200 border-t-slate-700" />
        <div>
          <h3 className="text-lg font-semibold text-slate-950">{title}</h3>
          {description ? <p className="text-sm text-slate-600">{description}</p> : null}
        </div>
      </div>
    </div>
  );
}
