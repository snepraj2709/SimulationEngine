interface ErrorStateProps {
  title: string;
  message: string;
}

export function ErrorState({ title, message }: ErrorStateProps) {
  return (
    <div className="panel border-red-200 bg-red-50/80 p-8">
      <h3 className="text-lg font-semibold text-red-900">{title}</h3>
      <p className="mt-2 text-sm text-red-800">{message}</p>
    </div>
  );
}
