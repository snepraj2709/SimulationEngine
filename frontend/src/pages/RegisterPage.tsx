import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router-dom";
import { z } from "zod";

import { registerUser } from "@/api/auth";
import { ApiError } from "@/api/client";
import { useAuthStore } from "@/store/auth-store";

const schema = z.object({
  full_name: z.string().min(2),
  email: z.string().email(),
  password: z.string().min(8),
});

type RegisterValues = z.infer<typeof schema>;

export function RegisterPage() {
  const navigate = useNavigate();
  const setSession = useAuthStore((state) => state.setSession);
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterValues>({ resolver: zodResolver(schema) });

  const mutation = useMutation({
    mutationFn: registerUser,
    onSuccess: (data) => {
      setSession(data.access_token, data.user);
      navigate("/dashboard");
    },
  });

  return (
    <div className="flex min-h-screen items-center justify-center px-6 py-10">
      <div className="panel w-full max-w-lg p-8">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Register</p>
        <h1 className="mt-3 text-3xl font-semibold text-slate-950">Create your workspace.</h1>
        <form onSubmit={handleSubmit((values) => mutation.mutate(values))} className="mt-8 space-y-4">
          <label className="block">
            <span className="mb-2 block text-sm font-medium text-slate-700">Full name</span>
            <input {...register("full_name")} className="w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm" />
            {errors.full_name ? <span className="mt-2 block text-sm text-red-600">{errors.full_name.message}</span> : null}
          </label>
          <label className="block">
            <span className="mb-2 block text-sm font-medium text-slate-700">Email</span>
            <input {...register("email")} className="w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm" />
            {errors.email ? <span className="mt-2 block text-sm text-red-600">{errors.email.message}</span> : null}
          </label>
          <label className="block">
            <span className="mb-2 block text-sm font-medium text-slate-700">Password</span>
            <input {...register("password")} type="password" className="w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm" />
            {errors.password ? <span className="mt-2 block text-sm text-red-600">{errors.password.message}</span> : null}
          </label>
          {mutation.error instanceof ApiError ? (
            <p className="text-sm text-red-600">{mutation.error.message}</p>
          ) : null}
          <button type="submit" className="w-full rounded-2xl bg-slate-950 px-4 py-3 text-sm font-semibold text-white">
            {mutation.isPending ? "Creating account..." : "Create account"}
          </button>
        </form>
        <p className="mt-6 text-sm text-slate-600">
          Already have an account?{" "}
          <Link to="/login" className="font-semibold text-slate-900 underline">
            Log in
          </Link>
        </p>
      </div>
    </div>
  );
}
