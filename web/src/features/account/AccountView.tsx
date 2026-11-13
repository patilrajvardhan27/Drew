import { useEffect, useState, type FormEvent } from "react";
import { api, type DocumentSummary } from "../../shared/api/client";
import { useAuth } from "../../shared/hooks/useAuth";
import { linkTo, navigate } from "../../shared/hooks/useRoute";
import { Button, Field, Skeleton } from "../../shared/ui";
import "./account.css";

function nextPath(): string {
  const next = new URLSearchParams(window.location.search).get("next");
  // Only same-site paths, so the parameter cannot send people elsewhere.
  return next && /^\/[a-z0-9/]*$/i.test(next) ? next : "/account";
}

export function AccountView() {
  const { user, ready, signOut } = useAuth();
  if (!ready) return <Skeleton height={200} style={{ marginTop: 48 }} />;
  if (!user) return <SignInForm />;

  return (
    <div className="account">
      <h1>Your documents</h1>
      <p className="muted">
        Signed in as {user.email}.{" "}
        <Button variant="quiet" className="inline-action" onClick={() => signOut().then(() => navigate("/"))}>
          Sign out
        </Button>
      </p>
      <DocumentList />
    </div>
  );
}

function DocumentList() {
  const [docs, setDocs] = useState<DocumentSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .listDocuments()
      .then(setDocs)
      .catch((err: Error) => setError(err.message));
  }, []);

  if (error) return <p className="alert">{error}</p>;
  if (!docs) return <Skeleton height={120} />;
  if (docs.length === 0) {
    return (
      <p className="muted">
        Nothing kept yet. <a {...linkTo("/")}>Upload a PDF</a> while signed in and it stays here.
      </p>
    );
  }
  return (
    <ul className="doc-list">
      {docs.map((doc) => (
        <li key={doc.id}>
          <a {...linkTo(`/d/${doc.id}`)}>{doc.name}</a>
          <span className="muted">
            {doc.page_count} pages · {new Date(doc.created_at + "Z").toLocaleDateString()}
          </span>
        </li>
      ))}
    </ul>
  );
}

function SignInForm() {
  const { signIn } = useAuth();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await signIn(mode, email, password);
      navigate(nextPath());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not sign in.");
      setBusy(false);
    }
  };

  const registering = mode === "register";
  return (
    <form className="account account-form" onSubmit={submit}>
      <h1>{registering ? "Create an account" : "Sign in"}</h1>
      <p className="muted">Documents in an account are kept until you delete them, not just 24 hours.</p>
      <Field label="Email">
        <input className="input" type="email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
      </Field>
      <Field label={registering ? "Password (at least 10 characters)" : "Password"}>
        <input
          className="input"
          type="password"
          autoComplete={registering ? "new-password" : "current-password"}
          minLength={10}
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
      </Field>
      {error && (
        <p className="alert" role="alert">
          {error}
        </p>
      )}
      <Button type="submit" disabled={busy}>
        {registering ? "Create account" : "Sign in"}
      </Button>
      <Button variant="quiet" onClick={() => setMode(registering ? "login" : "register")}>
        {registering ? "I already have an account" : "Create an account instead"}
      </Button>
    </form>
  );
}
