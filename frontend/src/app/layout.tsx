import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Credora | Banking, a little more personal",
  description:
    "Your everyday banking, investments and financial insights, thoughtfully connected. Credora customer banking experience.",
};
export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" data-scroll-behavior="smooth">
      <body>
        <a className="skip-link" href="#main">
          Skip to content
        </a>
        {children}
      </body>
    </html>
  );
}
