import { useState, type FormEvent, type ReactNode } from "react";
import { api } from "../../shared/api/client";
import { useAuth } from "../../shared/hooks/useAuth";
import { linkTo, navigate } from "../../shared/hooks/useRoute";
import { Button, Field } from "../../shared/ui";
import "./account.css";

function useSubmit(action: () => Promise<void>) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await action();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setBusy(false);
    }
  };
  return { busy, error, submit };
}

function Shell({ title, error, children, onSubmit }: { title: string; error: string | null; children: ReactNode; onSubmit: (e: FormEvent) => void }) {
  return (
    <form className="account account-form" onSubmit={onSubmit}>
      <h1>{title}</h1>
      {children}
      {error && (
        <p className="alert" role="alert">
          {error}
        </p>
      )}
    </form>
  );
}

export function ForgotPasswordView() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState<string | null>(null);
  const { busy, error, submit } = useSubmit(async () => setSent((await api.requestReset(email)).detail));

  return (
    <Shell title="Reset your password" error={error} onSubmit={submit}>
      {sent ? (
        <p role="status">{sent} The link works for one hour.</p>
      ) : (
        <>
          <p className="muted">Enter your account email and a reset link will be sent to it.</p>
          <Field label="Email">
            <input className="input" type="email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
          </Field>
          <Button type="submit" disabled={busy}>
            Send reset link
          </Button>
        </>
      )}
      <a {...linkTo("/account")}>Back to sign in</a>
    </Shell>
  );
}

export function ResetPasswordView() {
  const { refresh } = useAuth();
  const token = new URLSearchParams(window.location.search).get("token") ?? "";
  const [password, setPassword] = useState("");
  const { busy, error, submit } = useSubmit(async () => {
    await api.confirmReset(token, password);
    await refresh();
    navigate("/account");
  });

  if (!token) {
    return (
      <div className="account">
        <h1>Link incomplete</h1>
        <p className="muted">
          Open the link from the email in full, or <a {...linkTo("/forgot")}>ask for a new one</a>.
        </p>
      </div>
    );
  }
  return (
    <Shell title="Choose a new password" error={error} onSubmit={submit}>
      <p className="muted">This signs you out on every other device.</p>
      <Field label="New password (at least 10 characters)">
        <input
          className="input"
          type="password"
          autoComplete="new-password"
          minLength={10}
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
      </Field>
      <Button type="submit" disabled={busy}>
        Save password
      </Button>
    </Shell>
  );
}
