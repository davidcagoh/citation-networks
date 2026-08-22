"use client";

import { WorkbenchApp } from "@/features/workbench/WorkbenchApp";
import { createWorkbenchApi } from "@/lib/api";

const api = createWorkbenchApi();

export function ClientApp() {
  return <WorkbenchApp api={api} />;
}
