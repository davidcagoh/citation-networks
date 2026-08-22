import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "Literature Workbench",
  description: "A local-first, provenance-grounded literature synthesis workspace.",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return <html lang="en"><body style={{ margin: 0 }}>{children}</body></html>;
}
