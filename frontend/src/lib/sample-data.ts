export const accounts = [
  {
    id: "savings",
    name: "Everyday Savings",
    type: "Savings account",
    number: "4821",
    balance: 182450,
    branch: "Mumbai, Fort",
    ifsc: "SAMP0000482",
  },
  {
    id: "current",
    name: "Everyday Current",
    type: "Current account",
    number: "7093",
    balance: 64500,
    branch: "Mumbai, Fort",
    ifsc: "SAMP0000482",
  },
];
export type Transaction = {
  id: string;
  name: string;
  category: string;
  date: string;
  amount: number;
  account: string;
  initials: string;
};
export const transactions: Transaction[] = [
  {
    id: "TX1001",
    name: "Amazon India",
    category: "Shopping",
    date: "2026-09-25",
    amount: -1299,
    account: "savings",
    initials: "a",
  },
  {
    id: "TX1002",
    name: "September salary",
    category: "Income",
    date: "2026-09-24",
    amount: 65000,
    account: "savings",
    initials: "IN",
  },
  {
    id: "TX1003",
    name: "Blue Tokai Coffee",
    category: "Food & dining",
    date: "2026-09-23",
    amount: -480,
    account: "savings",
    initials: "BT",
  },
  {
    id: "TX1004",
    name: "Tata Power",
    category: "Bills",
    date: "2026-09-22",
    amount: -2400,
    account: "current",
    initials: "TP",
  },
  {
    id: "TX1005",
    name: "Uber",
    category: "Travel",
    date: "2026-09-21",
    amount: -365,
    account: "savings",
    initials: "U",
  },
  {
    id: "TX1006",
    name: "Freelance project",
    category: "Income",
    date: "2026-08-28",
    amount: 18000,
    account: "current",
    initials: "IN",
  },
  {
    id: "TX1007",
    name: "Fresh groceries",
    category: "Shopping",
    date: "2026-08-20",
    amount: -1850,
    account: "savings",
    initials: "FG",
  },
];
export const initialPayees = [
  { id: "p1", name: "Akhil Doshi", bank: "HDFC Bank", number: "9234" },
  { id: "p2", name: "Rahul Shah", bank: "ICICI Bank", number: "7211" },
];
export const spending = [
  { name: "Shopping", amount: 12800, color: "#7134a3" },
  { name: "Food & dining", amount: 8200, color: "#a371cb" },
  { name: "Bills & utilities", amount: 7400, color: "#d0b3e5" },
  { name: "Travel & other", amount: 5800, color: "#ebe0f3" },
];
export const products = [
  {
    name: "Fixed deposits",
    category: "Savings",
    risk: "Low",
    description: "Give your next milestone a little more certainty.",
    minimum: 10000,
  },
  {
    name: "Mutual funds",
    category: "Investment",
    risk: "Market-linked",
    description: "Build a habit today. Make room for tomorrow.",
    minimum: 500,
  },
  {
    name: "Life insurance",
    category: "Protection",
    risk: "Policy-dependent",
    description: "Plan a little further for the people you love.",
    minimum: 1000,
  },
  {
    name: "Bonds",
    category: "Investment",
    risk: "Issuer-dependent",
    description: "Explore a different way to diversify your portfolio.",
    minimum: 10000,
  },
  {
    name: "Stocks",
    category: "Investment",
    risk: "High",
    description: "Discover equity investing and understand the risks.",
    minimum: 100,
  },
];
