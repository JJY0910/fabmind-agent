export type NavSectionId = "diagnosis" | "reports-audit" | "system";

export type NavItemId =
  | "dashboard"
  | "equipment"
  | "active-incidents"
  | "checklists"
  | "approvals"
  | "audit-console"
  | "settings";

export type NavItem = {
  id: NavItemId;
  label: string;
  topbarLabel: string;
  href: string;
  testId: string;
  section: NavSectionId;
  activePathPrefixes: string[];
  badge?: string;
};

export const NAV_SECTIONS: Array<{ id: NavSectionId; label: string }> = [
  { id: "diagnosis", label: "DIAGNOSIS" },
  { id: "reports-audit", label: "REPORTS & AUDIT" },
  { id: "system", label: "SYSTEM" },
];

export const NAV_ITEMS: NavItem[] = [
  {
    id: "dashboard",
    label: "Dashboard",
    topbarLabel: "Dashboard",
    href: "/",
    testId: "sidebar-nav-dashboard",
    section: "diagnosis",
    activePathPrefixes: ["/", "/dashboard"],
  },
  {
    id: "equipment",
    label: "Equipment",
    topbarLabel: "Equipment Registry",
    href: "/equipment",
    testId: "sidebar-nav-equipment",
    section: "diagnosis",
    activePathPrefixes: ["/equipment"],
  },
  {
    id: "active-incidents",
    label: "Active Incidents",
    topbarLabel: "Active Incidents",
    href: "/active-incidents",
    testId: "sidebar-nav-active-incidents",
    section: "diagnosis",
    activePathPrefixes: ["/active-incidents"],
  },
  {
    id: "checklists",
    label: "Checklists",
    topbarLabel: "Checklist Runs",
    href: "/checklists",
    testId: "sidebar-nav-checklists",
    section: "reports-audit",
    activePathPrefixes: ["/checklists", "/checklist-runs"],
  },
  {
    id: "approvals",
    label: "Approvals",
    topbarLabel: "Approval Queue",
    href: "/approvals",
    testId: "sidebar-nav-approvals",
    section: "reports-audit",
    activePathPrefixes: ["/approvals", "/report-drafts"],
    badge: "3",
  },
  {
    id: "audit-console",
    label: "Audit Console",
    topbarLabel: "Audit Console",
    href: "/audit-events",
    testId: "sidebar-nav-audit-console",
    section: "system",
    activePathPrefixes: ["/audit-events"],
  },
  {
    id: "settings",
    label: "Settings",
    topbarLabel: "System Safety Settings",
    href: "/settings",
    testId: "sidebar-nav-settings",
    section: "system",
    activePathPrefixes: ["/settings"],
  },
];

export function isNavItemActive(item: NavItem, pathname: string | null): boolean {
  const currentPath = normalizePathname(pathname);

  if (item.id === "dashboard") {
    return currentPath === "/" || currentPath === "/dashboard";
  }

  return item.activePathPrefixes.some(
    (prefix) => currentPath === prefix || currentPath.startsWith(`${prefix}/`),
  );
}

export function getCurrentNavItem(pathname: string | null): NavItem {
  return NAV_ITEMS.find((item) => isNavItemActive(item, pathname)) ?? NAV_ITEMS[0];
}

function normalizePathname(pathname: string | null): string {
  if (!pathname) return "/";
  const normalized = pathname.split("?")[0].replace(/\/+$/, "");
  return normalized === "" ? "/" : normalized;
}
