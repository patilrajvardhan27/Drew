import type { ReactNode } from "react";
import { AccountView } from "./features/account/AccountView";
import { EditorView } from "./features/editor/EditorView";
import { CopyrightPage, PrivacyPage, TermsPage } from "./features/pages/SitePages";
import { UploadView } from "./features/upload/UploadView";
import { AuthProvider, useAuth } from "./shared/hooks/useAuth";
import { linkTo, usePath } from "./shared/hooks/useRoute";

const STATIC_PAGES: Record<string, () => ReactNode> = {
  "/terms": TermsPage,
  "/privacy": PrivacyPage,
  "/copyright": CopyrightPage,
  "/account": AccountView,
};

function route(path: string): ReactNode {
  const editor = path.match(/^\/d\/([a-f0-9]+)$/);
  if (editor) return <EditorView key={editor[1]} id={editor[1]} />;
  const Page = STATIC_PAGES[path];
  if (Page) return <Page />;
  if (path === "/") return <UploadView />;
  return (
    <div className="prose">
      <h1>Page not found</h1>
      <a {...linkTo("/")}>Back to upload</a>
    </div>
  );
}

export function App() {
  return (
    <AuthProvider>
      <Shell />
    </AuthProvider>
  );
}

function AccountLink() {
  const { user, ready } = useAuth();
  if (!ready) return null;
  return <a {...linkTo("/account")}>{user ? "Your documents" : "Sign in"}</a>;
}

function Shell() {
  const path = usePath();
  return (
    <div className="shell">
      <nav className="nav" aria-label="Main">
        <a className="brand" {...linkTo("/")}>
          Redraft
        </a>
        <span className="nav-links">
          <a {...linkTo("/")}>New document</a>
          <AccountLink />
        </span>
      </nav>
      <main>{route(path)}</main>
      <footer className="footer">
        <a {...linkTo("/terms")}>Terms</a>
        <a {...linkTo("/privacy")}>Privacy</a>
        <a {...linkTo("/copyright")}>Copyright</a>
        <span className="muted">Independent project. Not affiliated with Adobe.</span>
      </footer>
    </div>
  );
}
