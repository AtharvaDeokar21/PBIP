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
};
