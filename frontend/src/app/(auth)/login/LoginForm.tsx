"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import { AuthShell } from "@/components/auth/AuthShell";
import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { authApi, ApiError } from "@/lib/api";
import { saveSession } from "@/lib/auth";

export function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (searchParams.get("pending") === "1") {
      setInfo(
        "Your registration was submitted. Sign in after an administrator approves your account."
      );
      const pendingEmail = searchParams.get("email");
      if (pendingEmail) setEmail(pendingEmail);
    }
  }, [searchParams]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const tokens = await authApi.login({ email, password });
      saveSession(tokens);
      router.push("/");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthShell title="Sign in" subtitle="Access your compliance dashboard">
      <form onSubmit={handleSubmit} className="space-y-5">
        {info && <Alert variant="info">{info}</Alert>}
        {error && <Alert variant="error">{error}</Alert>}
        <div>
          <label className="mb-1.5 block text-sm font-medium text-text-secondary">Email</label>
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="input-field"
            placeholder="you@company.com"
          />
        </div>
        <div>
          <label className="mb-1.5 block text-sm font-medium text-text-secondary">Password</label>
          <input
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="input-field"
            placeholder="••••••••"
          />
        </div>
        <Button type="submit" className="w-full" loading={loading}>
          Sign in
        </Button>
      </form>
      <p className="mt-6 text-center text-sm text-text-muted">
        No account?{" "}
        <Link href="/signup" className="font-semibold text-text-accent hover:text-primary-300">
          Create one
        </Link>
      </p>
    </AuthShell>
  );
}
