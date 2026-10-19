import type { AdminSnapshot, Customer, Segment, Risk, Interest } from "./types";
export const AS_OF = "2026-10-05";
const records: [string, Segment, Risk, number, number, number, Interest][] = [
  ["Aarav Shah", "Premium", "Low", 18, 95000, 38200, "Investments"],
  ["Diya Mehta", "High Value", "High", 82, 145000, 62400, "Loans"],
  ["Rohan Kapoor", "Standard", "Medium", 48, 62000, 28100, "Savings"],
  ["Ananya Rao", "Premium", "Low", 22, 108000, 43100, "Insurance"],
  ["Kabir Joshi", "High Value", "High", 76, 180000, 75800, "Investments"],
  ["Meera Nair", "Standard", "Low", 15, 54000, 22300, "Savings"],
  ["Ishaan Patel", "Premium", "Medium", 53, 87000, 35600, "Loans"],
  ["Sana Khan", "Standard", "Low", 12, 58000, 24500, "Insurance"],
  ["Vivaan Desai", "High Value", "Medium", 42, 210000, 88300, "Investments"],
  ["Aditi Kulkarni", "Premium", "Low", 20, 99000, 40900, "Savings"],
  ["Arjun Singh", "Standard", "High", 71, 68000, 31400, "Loans"],
  ["Nisha Thomas", "Premium", "Low", 17, 112000, 45700, "Insurance"],
];
const customers: Customer[] = records.map(
  ([name, segment, risk, riskScore, income, spending, interest], i) => ({
    id: `C${1001 + i}`,
    name,
    email: `${name.toLowerCase().replace(" ", ".")}@example.com`,
    segment,
    risk,
    riskScore,
    income,
    spending,
    spendingInsights: [],
    monthlyIncomeTrend: [],
    monthlySpendingTrend: [],
    interest,
    products: [
      "Savings account",
      interest === "Loans"
        ? "Personal loan"
        : interest === "Investments"
          ? "Mutual fund"
          : interest === "Insurance"
            ? "Life insurance"
            : "Fixed deposit",
      ...(segment === "High Value" ? ["Current account"] : []),
    ],
    accounts: [
      {
        id: `A${i + 1}S`,
        type: "Savings",
        lastFour: String(4821 + i * 137),
        balance: income * 2 + (i + 1) * 4500,
        status: "Active",
      },
      ...(segment === "High Value"
        ? [
            {
              id: `A${i + 1}C`,
              type: "Current",
              lastFour: String(7093 + i * 39),
              balance: income * 1.4,
              status: "Active" as const,
            },
          ]
        : []),
    ],
  }),
);
const paths = {
  Savings: ["Dashboard", "Accounts", "Transactions"],
  Loans: ["Dashboard", "Loans", "EMI Calculator"],
  Investments: ["Dashboard", "Investments", "Mutual Funds"],
  Insurance: ["Dashboard", "Wealth", "Insurance"],
};
const sessions = customers.flatMap((c, i) =>
  Array.from({ length: 30 }, (_, j) => ({
    id: `S${i}-${j}`,
    customerId: c.id,
    date: new Date(Date.UTC(2026, 6, 8 + j * 3 + (i % 3)))
      .toISOString()
      .slice(0, 10),
    seconds: 120 + ((i * 19 + j * 13) % 300),
    returning: j > 0,
    path: paths[c.interest ?? "Savings"],
    product: c.interest,
    views: 2 + ((i + j) % 5),
    clicks: 1 + ((i + j) % 3),
  })),
);
const merchants = [
  "Monthly salary",
  "Fresh groceries",
  "Amazon India",
  "Electricity bill",
  "Metro travel",
  "Cinema",
  "Online transfer",
];
const categories = [
  "Income",
  "Food",
  "Shopping",
  "Utilities",
  "Travel",
  "Entertainment",
  "Other",
];
const transactions = customers.flatMap((c, i) =>
  ["07", "08", "09", "10"].flatMap((month, m) =>
    Array.from({ length: 7 }, (_, j) => ({
      id: `TX${1000 + i * 10 + j}-${month}`,
      customerId: c.id,
      date: `2026-${month}-${String(month === "10" ? 5 - (j % 5) : 24 + j).padStart(2, "0")}`,
      merchant: merchants[j],
      category: categories[j],
      amount:
        j === 0
          ? Math.round(c.income * [0.95, 0.98, 1, 1][m])
          : Math.round(
              c.spending *
                [0.9, 0.94, 1, 1][m] *
                [0, 0.12, 0.24, 0.13, 0.09, 0.07, 0.35][j],
            ),
      type: j === 0 ? ("Credit" as const) : ("Debit" as const),
      status: "Completed" as const,
      risk:
        j === 6 && c.risk === "High" && month === "10"
          ? ("High" as const)
          : ("Low" as const),
    })),
  ),
);
export const adminSampleData: AdminSnapshot = {
  asOf: AS_OF,
  customers,
  transactions,
  sessions,
  alerts: [
    {
      id: "FA-2041",
      customerId: "C1002",
      type: "Unusual transfer amount",
      severity: "Critical",
      date: "2026-10-05T09:42:00+05:30",
      status: "Open",
      domain: "Fraud",
    },
    {
      id: "FA-2040",
      customerId: "C1005",
      type: "New sign-in location",
      severity: "High",
      date: "2026-10-05T09:18:00+05:30",
      status: "In review",
      domain: "Fraud",
    },
    {
      id: "CA-1088",
      customerId: "C1011",
      type: "Customer review overdue",
      severity: "High",
      date: "2026-10-05T08:56:00+05:30",
      status: "Open",
      domain: "Compliance",
    },
    {
      id: "FA-2039",
      customerId: "C1007",
      type: "Repeated login failures",
      severity: "Medium",
      date: "2026-10-04T17:20:00+05:30",
      status: "In review",
      domain: "Fraud",
    },
    {
      id: "CA-1087",
      customerId: "C1003",
      type: "Account documentation review",
      severity: "Medium",
      date: "2026-10-04T14:08:00+05:30",
      status: "Open",
      domain: "Compliance",
    },
    {
      id: "FA-2038",
      customerId: "C1001",
      type: "Unrecognized device",
      severity: "Low",
      date: "2026-10-03T11:35:00+05:30",
      status: "Resolved",
      domain: "Fraud",
    },
  ],
  activity: [
    {
      id: "E1",
      title: "Fraud alert generated",
      detail: "FA-2041 · unusual transfer amount",
      date: "2026-10-05T09:42:00+05:30",
      customerId: "C1002",
    },
    {
      id: "E2",
      title: "Investigation opened",
      detail: "FA-2040 · location review",
      date: "2026-10-05T09:25:00+05:30",
      customerId: "C1005",
    },
    {
      id: "E3",
      title: "Compliance exception created",
      detail: "CA-1088 · customer review",
      date: "2026-10-05T08:56:00+05:30",
      customerId: "C1011",
    },
    {
      id: "E4",
      title: "Alert resolved",
      detail: "FA-2038 · device recognized",
      date: "2026-10-03T12:10:00+05:30",
      customerId: "C1001",
    },
  ],
};
