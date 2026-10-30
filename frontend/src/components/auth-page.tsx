"use client";
import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  ArrowRight,
  Eye,
  EyeOff,
  ShieldCheck,
  Sparkles,
  Users,
  Building2,
} from "lucide-react";
import { Brand } from "./ui";

import { adminLogin, storeToken } from "@/lib/admin/api";
import {
  customerLogin,
  customerRegister,
  storeCustomerToken,
} from "@/lib/customer/api";

type AuthMode =
  "login" | "register" | "forgot-password" | "session-expired" | "admin-login";
export default function AuthPage({ mode }: { mode: AuthMode }) {
  const router = useRouter();
  const [visible, setVisible] = useState(false);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const isAdmin = mode === "admin-login";
  const isRegister = mode === "register";
  const isRecovery = mode === "forgot-password";
  const expired = mode === "session-expired";

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (mode === "admin-login") {
      const form = event.currentTarget;
      const email = (form.elements.namedItem("email") as HTMLInputElement).value;
      const password = (form.elements.namedItem("password") as HTMLInputElement).value;
      setLoading(true);
      setMessage("");
      try {
        const res = await adminLogin(email, password);
        if (res.role !== "ADMIN" && res.role !== "RELATIONSHIP_MANAGER") {
          setMessage("Access denied. This portal is for administrators only.");
          return;
        }
        storeToken(res.access_token);
        router.push("/admin/dashboard");
      } catch {
        setMessage("Invalid email or password. Please try again.");
      } finally {
        setLoading(false);
      }
      return;
    }

    if (mode === "login") {
      const form = event.currentTarget;
      const email = (
        form.elements.namedItem("email") as HTMLInputElement
      ).value;
      const password = (
        form.elements.namedItem("password") as HTMLInputElement
      ).value;
      setLoading(true);
      setMessage("");
      try {
        const res = await customerLogin(email, password);
        if (res.role !== "CUSTOMER") {
          setMessage(
            "This account does not have customer access. Use Admin login instead.",
          );
          return;
        }
        storeCustomerToken(res.access_token);
        router.push("/portal/dashboard");
      } catch (err) {
        setMessage(
          err instanceof Error
            ? err.message
            : "Invalid email or password. Please try again.",
        );
      } finally {
        setLoading(false);
      }
      return;
    }

    if (mode === "register") {
      const form = event.currentTarget;
      const firstName = (
        form.elements.namedItem("firstName") as HTMLInputElement
      ).value;
      const lastName = (
        form.elements.namedItem("lastName") as HTMLInputElement
      ).value;
      const email = (
        form.elements.namedItem("email") as HTMLInputElement
      ).value;
      const password = (
        form.elements.namedItem("password") as HTMLInputElement
      ).value;
      setLoading(true);
      setMessage("");
      try {
        await customerRegister(
          email,
          password,
          firstName,
          lastName,
        );
        // Backend /auth/register creates user & customer, but does not return JWT.
        // Immediately log in to obtain access_token for portal session.
        const loginRes = await customerLogin(email, password);
        storeCustomerToken(loginRes.access_token);
        router.push("/portal/dashboard");
      } catch (err) {
        setMessage(
          err instanceof Error
            ? err.message
            : "Registration failed. Please check your details and try again.",
        );
      } finally {
        setLoading(false);
      }
      return;
    }

    setMessage(
      isRecovery
        ? "Password recovery is not connected yet. No reset email has been sent."
        : `Sign-in is not connected yet.`,
    );
  }

  return (
    <div className="auth-layout">
      <aside className="auth-story">
        <Brand light />
        <div>
          <span className="eyebrow">
            {isAdmin
              ? "THE PEOPLE BEHIND BETTER BANKING"
              : "YOUR MONEY. MORE POSSIBILITIES."}
          </span>
          <h1>
            {isAdmin ? (
              <>
                Better oversight.
                <br />
                Thoughtful decisions.
                <br />
                <em>Banking, together.</em>
              </>
            ) : (
              <>
                A little clarity.
                <br />A little confidence.
                <br />
                <em>A lot more you.</em>
              </>
            )}
          </h1>
          <p>
            {isAdmin
              ? "A dedicated entry point for authorized banking administrators."
              : "Everyday banking and a brighter financial future. Thoughtfully connected."}
          </p>
          <div className="auth-quote">
            <Sparkles size={23} />
            <p>
              {isAdmin ? (
                "One team. A clearer view."
              ) : (
                <>
                  Big plans begin with
                  <br />
                  small, everyday steps.
                </>
              )}
            </p>
          </div>
        </div>
        <small>Credora · Banking, thoughtfully connected.</small>
      </aside>
      <main id="main" className="auth-main">
        <Link className="text-link" href="/">
          <ArrowLeft size={16} /> Back to home
        </Link>
        <div className="auth-form">
          <nav className="auth-access-tabs" aria-label="Login type">
            <Link
              href="/login"
              className={!isAdmin ? "active" : ""}
              aria-current={!isAdmin ? "page" : undefined}
            >
              <Users size={17} /> Customer
            </Link>
            <Link
              href="/admin/login"
              className={isAdmin ? "active" : ""}
              aria-current={isAdmin ? "page" : undefined}
            >
              <Building2 size={17} /> Admin
            </Link>
          </nav>
          <span className="icon-tile lavender">
            {isAdmin ? <Building2 size={24} /> : <ShieldCheck size={24} />}
          </span>
          <span className="eyebrow">
            {isAdmin ? "INTERNAL BANKING PORTAL" : "YOUR PERSONAL BANKING"}
          </span>
          <h1>
            {isAdmin
              ? "Admin login"
              : isRegister
                ? "Create your account"
                : isRecovery
                  ? "Forgot your password?"
                  : expired
                    ? "Let’s reconnect."
                    : "Customer login"}
          </h1>
          <p className="muted">
            {isAdmin
              ? "Sign in with your administrator email and password."
              : isRegister
                ? "Start your next chapter with Credora."
                : isRecovery
                  ? "Enter your email address to request a password reset."
                  : expired
                    ? "Sign in again to continue to your account."
                    : "Enter your customer email and password."}
          </p>
          {expired ? (
            <Link href="/login" className="button">
              Back to sign in <ArrowRight size={16} />
            </Link>
          ) : (
            <form method="post" onSubmit={submit} onChange={() => setMessage("")}>
              {isRegister && (
                <div className="form-two">
                  <label>
                    First name
                    <input
                      name="firstName"
                      required
                      autoComplete="given-name"
                      placeholder="Your first name"
                      maxLength={100}
                    />
                  </label>
                  <label>
                    Last name
                    <input
                      name="lastName"
                      required
                      autoComplete="family-name"
                      placeholder="Your last name"
                      maxLength={100}
                    />
                  </label>
                </div>
              )}
              <label>
                {isAdmin ? "Administrator email" : "Email address"}
                <input
                  name="email"
                  required
                  type="email"
                  autoComplete="username"
                  placeholder={
                    isAdmin ? "admin@credora.com" : "you@example.com"
                  }
                  maxLength={254}
                />
              </label>
              {!isRecovery && (
                <label>
                  Password
                  <div className="password-input">
                    <input
                      name="password"
                      required
                      type={visible ? "text" : "password"}
                      minLength={8}
                      maxLength={72}
                      autoComplete={
                        isRegister ? "new-password" : "current-password"
                      }
                      placeholder="At least 8 characters"
                    />
                    <button
                      type="button"
                      className="icon-button"
                      aria-label={visible ? "Hide password" : "Show password"}
                      onClick={() => setVisible(!visible)}
                    >
                      {visible ? <EyeOff size={18} /> : <Eye size={18} />}
                    </button>
                  </div>
                </label>
              )}
              {mode === "login" && (
                <div className="auth-links">
                  <span />
                  <Link href="/forgot-password">Forgot password?</Link>
                </div>
              )}
              {isAdmin && (
                <p className="field-help admin-help">
                  Access is provisioned by your organization. Contact your
                  system administrator if you need help signing in.
                </p>
              )}
              {message && (
                <p className="form-error" role="alert">
                  {message}
                </p>
              )}
              <button className="button full-width" disabled={loading}>
                {isRecovery
                  ? "Send reset link"
                  : isRegister
                    ? loading
                      ? "Creating account…"
                      : "Sign up"
                    : isAdmin
                      ? loading
                        ? "Signing in…"
                        : "Admin login"
                      : loading
                        ? "Signing in…"
                        : "Log in"}
                <ArrowRight size={17} />
              </button>
            </form>
          )}
          {!isAdmin && !expired && (
            <p className="auth-bottom">
              {isRegister ? "Already have an account?" : "New to Credora?"}{" "}
              <Link href={isRegister ? "/login" : "/register"}>
                {isRegister ? "Log in" : "Sign up"}
              </Link>
            </p>
          )}
          <span className="security-note">
            <ShieldCheck size={15} /> Never share your password or OTP.
          </span>
        </div>
        <small className="muted">© 2026 Credora · Built around you.</small>
      </main>
    </div>
  );
}
