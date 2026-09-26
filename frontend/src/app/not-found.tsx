import Link from "next/link";
import { Brand } from "@/components/ui";
export default function NotFound() {
  return (
    <main id="main" className="not-found">
      <Brand />
      <span className="eyebrow">404 · A SMALL DETOUR</span>
      <h1>Let’s get you back on track.</h1>
      <p className="muted">We couldn’t find that page.</p>
      <Link className="button" href="/">
        Back to home
      </Link>
    </main>
  );
}
