export type Risk = "Low" | "Medium" | "High" | "Critical";
export type Segment = "Standard" | "Premium" | "High Value";
export type Interest = "Savings" | "Loans" | "Investments" | "Insurance";
export type Customer = {
  id: string;
  name: string;
  email: string;
  segment: Segment;
  risk: Risk | null;
  riskScore: number;
  income: number;
  spending: number;
  spendingInsights: { category: string; amount: number }[];
  monthlyIncomeTrend: { month: string; amount: number }[];
  monthlySpendingTrend: { month: string; amount: number }[];
  interest: Interest | null;
  products: string[];
  accounts: {
    id: string;
    type: string;
    lastFour: string;
    balance: number;
    status: "Active" | "Dormant";
  }[];
};
export type Transaction = {
  id: string;
  customerId: string;
  date: string;
  merchant: string;
  category: string;
  amount: number;
  type: "Credit" | "Debit";
  status: "Completed" | "Pending";
  risk: Risk | null;
};
export type Alert = {
  id: string;
  customerId: string;
  type: string;
  severity: Risk;
  date: string;
  status: "Open" | "In review" | "Resolved";
  domain: "Fraud" | "Compliance";
};
export type Session = {
  id: string;
  customerId: string;
  date: string;
  seconds: number;
  returning: boolean;
  path: string[];
  product: Interest | null;
  views: number;
  clicks: number;
};
export type OverviewSummary = {
  totalCustomers: number;
  activeFraudAlerts: number;
  highRiskCustomers: number;
  openInvestigations: number;
  complianceAlerts: number;
  engagementPct: number;
};

export type AdminSnapshot = {
  asOf: string;
  customers: Customer[];
  transactions: Transaction[];
  alerts: Alert[];
  sessions: Session[];
  activity: {
    id: string;
    title: string;
    detail: string;
    date: string;
    customerId: string;
  }[];
  summary?: OverviewSummary;
};

export type InvestigationStatus =
  | "Open"
  | "In review"
  | "Escalated"
  | "Resolved"
  | "False positive";

export type InvestigationItem = {
  id: string;
  alertId: string;
  customerId: string | null;
  customerName: string;
  type: string;
  severity: Risk;
  status: InvestigationStatus;
  assignedTo: string;
  openedAt: string;
  updatedAt: string;
  notes: string[];
  riskScore: number;
  amount?: number;
};

export type InvestigationListResponse = {
  total: number;
  page: number;
  pageSize: number;
  items: InvestigationItem[];
};

export type CanonicalAlertStatus =
  | "OPEN"
  | "IN_REVIEW"
  | "ESCALATED"
  | "RESOLVED"
  | "FALSE_POSITIVE";

export type FraudAlertUpdatePayload = {
  status: CanonicalAlertStatus;
  resolution_notes?: string | null;
};

export type FraudAlertResponse = {
  id: string;
  fraud_event_id: string;
  customer_id: string;
  status: string;
  priority: number;
  assigned_to: string | null;
  created_at: string;
  updated_at: string;
  resolved_at: string | null;
  resolution_notes: string | null;
};

export type ComplianceCategory =
  | "KYC"
  | "AML"
  | "Reporting"
  | "Documentation"
  | "Transaction";

export type ComplianceAlertItem = {
  id: string;
  customerId: string;
  customerName: string;
  type: string;
  category: ComplianceCategory;
  severity: "Low" | "Medium" | "High" | "Critical";
  status: "Open" | "In review" | "Resolved";
  dueDate: string;
  raisedAt: string;
  description: string;
  assignedTo: string;
};

export type ComplianceSummary = {
  openCount: number;
  criticalCount: number;
  resolvedCount: number;
  categoryCounts: Record<string, number>;
};

export type ComplianceAlertListResponse = {
  total: number;
  page: number;
  pageSize: number;
  items: ComplianceAlertItem[];
  summary: ComplianceSummary;
};

export type AuditOutcome = "Success" | "Failure" | "Warning";

export type AuditEntry = {
  id: string;
  actor: string;
  actorRole: string;
  action: string;
  resource: string;
  resourceId: string;
  outcome: AuditOutcome;
  ipAddress: string;
  timestamp: string;
  customerId?: string;
};

export type AuditSummary = {
  totalEvents: number;
  successCount: number;
  failureCount: number;
  warningCount: number;
  availableActors: string[];
  availableActions: string[];
};

export type AuditLogListResponse = {
  total: number;
  page: number;
  pageSize: number;
  items: AuditEntry[];
  summary: AuditSummary;
};

export type SecurityChannel =
  | "Mobile app"
  | "Net banking"
  | "ATM"
  | "API"
  | "Unknown";

export type SecurityEventItem = {
  id: string;
  eventId?: string;
  userId?: string | null;
  customerId?: string | null;
  customerName: string;
  eventType: string;
  channel: string;
  severity: Risk;
  status: string;
  detectedAt: string;
  description: string;
  location: string;
  device: string;
  ipAddress: string;
};

export type SecuritySummary = {
  totalEvents: number;
  criticalCount: number;
  requiresReviewCount: number;
  loggedCount: number;
  openCount: number;
  resolvedCount: number;
  severityCounts: Record<string, number>;
  channelCounts: Record<string, number>;
};

export type SecurityEventListResponse = {
  total: number;
  page: number;
  pageSize: number;
  items: SecurityEventItem[];
  summary: SecuritySummary;
};
