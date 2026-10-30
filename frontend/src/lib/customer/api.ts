/**
 * Typed API client for the customer-facing portal.
 * Mirrors every endpoint in docs/api/customer/.
 *
 * Base URL: NEXT_PUBLIC_API_URL env var (default: http://127.0.0.1:8000/api/v1)
 */

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000/api/v1";
const TOKEN_KEY = "customer_token";

export function storeCustomerToken(token: string) {
  if (typeof localStorage !== "undefined") localStorage.setItem(TOKEN_KEY, token);
}
export function clearCustomerToken() {
  if (typeof localStorage !== "undefined") localStorage.removeItem(TOKEN_KEY);
}
export function getCustomerToken(): string | null {
  if (typeof localStorage === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getCustomerToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init?.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = "Bearer " + token;
  const res = await fetch(BASE + path, { ...init, headers });
  if (!res.ok) {
    if (res.status === 204) return undefined as T;
    const body = await res.text().catch(() => "");
    let detail = body;
    try {
      const p = JSON.parse(body);
      detail = p?.detail ?? body;
    } catch {
      /* raw text */
    }
    throw new Error(detail || "API error " + res.status);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

// ─── Types ─────────────────────────────────────────────────────────────────

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user_id: string;
  role: string;
}

export interface CustomerProfile {
  id: string;
  customer_number: string;
  first_name: string;
  last_name: string;
  email: string;
  phone: string | null;
  address: string | null;
  city: string | null;
  state: string | null;
  postal_code: string | null;
  occupation: string | null;
  employment_type: string | null;
  annual_income: string | null;
  risk_profile: string | null;
  customer_segment: string | null;
}

export interface CustomerUpdate {
  phone?: string | null;
  address?: string | null;
  city?: string | null;
  state?: string | null;
  postal_code?: string | null;
  occupation?: string | null;
}

export interface CustomerSummary {
  currency: string;
  total_balance: string;
  total_available_balance: string;
  total_accounts: number;
  active_accounts: number;
  balances_by_type: {
    account_type: string;
    balance: string;
    account_count: number;
  }[];
  month_to_date_credits: string;
  month_to_date_debits: string;
  active_payees: number;
  open_loan_applications: number;
  total_invested: string;
}

export interface Account {
  id: string;
  account_number: string;
  account_type: string;
  currency: string;
  balance: string;
  available_balance: string;
  status: string;
  opened_at: string | null;
  created_at: string;
}

export interface AccountListResponse {
  items: Account[];
  total: number;
}

export interface Transaction {
  id: string;
  account_id: string;
  transaction_reference: string;
  transaction_type: "DEBIT" | "CREDIT";
  amount: string;
  currency: string;
  category: string | null;
  description: string | null;
  merchant_name: string | null;
  merchant_category: string | null;
  transaction_status: string;
  transaction_date: string;
  location: string | null;
  channel: string | null;
}

export interface TransactionFilters {
  page?: number;
  page_size?: number;
  category?: string;
  transaction_type?: string;
  transaction_status?: string;
  start_date?: string;
  end_date?: string;
  min_amount?: string;
  max_amount?: string;
  search?: string;
}

export interface Page<T> {
  items: T[];
  page: number;
  page_size: number;
  total: number;
}

export interface Payee {
  id: string;
  name: string;
  account_number: string;
  bank_name: string;
  ifsc_code: string;
  nickname: string;
  is_verified: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface PayeeCreate {
  name: string;
  account_number: string;
  bank_name: string;
  ifsc_code: string;
  nickname: string;
}

export interface PayeeUpdate {
  name?: string;
  bank_name?: string;
  nickname?: string;
}

export interface Transfer {
  id: string;
  source_account_id: string;
  destination_account_id: string | null;
  payee_id: string | null;
  amount: string;
  transfer_type: "IMMEDIATE" | "SCHEDULED";
  status: string;
  reference_number: string;
  scheduled_at: string | null;
  executed_at: string | null;
  created_at: string;
}

export interface TransferCreate {
  source_account_id: string;
  payee_id?: string;
  destination_account_id?: string;
  amount: number;
  transfer_type?: "IMMEDIATE" | "SCHEDULED";
  scheduled_at?: string;
  remarks?: string;
}

export interface Biller {
  id: string;
  name: string;
  category: string | null;
  provider_code: string;
  is_active: boolean;
}

export interface BillPaymentCreate {
  account_id: string;
  biller_id: string;
  amount: number;
  due_date?: string;
}

export interface BillPayment {
  id: string;
  account_id: string;
  biller_id: string;
  amount: string;
  status: string;
  due_date: string | null;
  paid_at: string | null;
  reference_number: string;
  created_at: string;
}

export interface LoanProduct {
  id: string;
  name: string;
  loan_type: string;
  min_amount: string;
  max_amount: string;
  interest_rate: string;
  min_tenure_months: number;
  max_tenure_months: number;
  description: string | null;
}

export interface LoanEligibilityRequest {
  loan_product_id: string;
  requested_amount: number;
  tenure_months: number;
}

export interface LoanEligibilityResponse {
  loan_product_id: string;
  eligible: boolean;
  eligibility_score: string;
  interest_rate: string;
  estimated_emi: string;
  reasons: string[];
}

export interface LoanApplication {
  id: string;
  loan_product_id: string;
  requested_amount: string;
  tenure_months: number;
  interest_rate: string | null;
  emi_amount: string | null;
  eligibility_score: string | null;
  status: string;
  application_date: string;
  approved_at: string | null;
  rejection_reason: string | null;
}

export interface InvestmentProduct {
  id: string;
  name: string;
  product_type: string;
  risk_level: string;
  expected_return: string | null;
  minimum_investment: string;
  lock_in_period: string | null;
  description: string | null;
}

export interface InvestmentHolding {
  id: string;
  investment_product_id: string;
  amount_invested: string;
  units: string | null;
  purchase_price: string | null;
  current_value: string | null;
  purchase_date: string;
  status: string;
}

export interface InvestmentCreate {
  investment_product_id: string;
  amount_invested: number;
  source_account_id?: string;
}

export interface InsuranceProduct {
  id: string;
  name: string;
  insurance_type: string;
  risk_level: string;
  description: string | null;
}

export interface Recommendation {
  id: string;
  product_type: string;
  product_id: string;
  recommendation_type: string;
  score: string;
  reason: string | null;
  status: string;
  created_at: string;
  expires_at: string | null;
}

// ─── Auth ──────────────────────────────────────────────────────────────────

export async function customerLogin(
  email: string,
  password: string,
): Promise<AuthResponse> {
  return apiFetch("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export interface RegisterResponse {
  user_id: string;
  customer_id: string;
  email: string;
  role: string;
}

export async function customerRegister(
  email: string,
  password: string,
  first_name: string,
  last_name: string,
): Promise<RegisterResponse> {
  return apiFetch("/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password, first_name, last_name }),
  });
}

// ─── Customer ──────────────────────────────────────────────────────────────

export const fetchProfile = (): Promise<CustomerProfile> =>
  apiFetch("/customers/me");

export const updateProfile = (data: CustomerUpdate): Promise<CustomerProfile> =>
  apiFetch("/customers/me", { method: "PATCH", body: JSON.stringify(data) });

export const fetchSummary = (): Promise<CustomerSummary> =>
  apiFetch("/customers/me/summary");

// ─── Accounts ─────────────────────────────────────────────────────────────

export const fetchAccounts = (): Promise<AccountListResponse> =>
  apiFetch("/accounts");

export const fetchAccount = (id: string): Promise<Account> =>
  apiFetch("/accounts/" + id);

export function fetchTransactions(
  accountId: string,
  filters: TransactionFilters = {},
): Promise<Page<Transaction>> {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([k, v]) => {
    if (v !== undefined && v !== "") params.set(k, String(v));
  });
  const qs = params.toString();
  return apiFetch(
    "/accounts/" + accountId + "/transactions" + (qs ? "?" + qs : ""),
  );
}

export const fetchTransaction = (id: string): Promise<Transaction> =>
  apiFetch("/transactions/" + id);

// ─── Payees ────────────────────────────────────────────────────────────────

export const fetchPayees = (): Promise<Payee[]> => apiFetch("/payees");

export const createPayee = (data: PayeeCreate): Promise<Payee> =>
  apiFetch("/payees", { method: "POST", body: JSON.stringify(data) });

export const updatePayee = (id: string, data: PayeeUpdate): Promise<Payee> =>
  apiFetch("/payees/" + id, { method: "PATCH", body: JSON.stringify(data) });

export const deletePayee = (id: string): Promise<void> =>
  apiFetch("/payees/" + id, { method: "DELETE" });

// ─── Transfers ─────────────────────────────────────────────────────────────

export const createTransfer = (data: TransferCreate): Promise<Transfer> =>
  apiFetch("/transfers", { method: "POST", body: JSON.stringify(data) });

export function fetchTransfers(
  page = 1,
  page_size = 20,
  status?: string,
): Promise<Page<Transfer>> {
  const params = new URLSearchParams({
    page: String(page),
    page_size: String(page_size),
  });
  if (status) params.set("status", status);
  return apiFetch("/transfers?" + params.toString());
}

export const fetchTransfer = (id: string): Promise<Transfer> =>
  apiFetch("/transfers/" + id);

export const cancelTransfer = (id: string): Promise<Transfer> =>
  apiFetch("/transfers/" + id + "/cancel", { method: "POST" });

// ─── Bills ─────────────────────────────────────────────────────────────────

export const fetchBillers = (category?: string): Promise<Biller[]> =>
  apiFetch("/billers" + (category ? "?category=" + encodeURIComponent(category) : ""));

export const payBill = (data: BillPaymentCreate): Promise<BillPayment> =>
  apiFetch("/bills/pay", { method: "POST", body: JSON.stringify(data) });

export const fetchBillHistory = (
  page = 1,
  page_size = 20,
): Promise<Page<BillPayment>> =>
  apiFetch("/bills/history?page=" + page + "&page_size=" + page_size);

// ─── Loans ─────────────────────────────────────────────────────────────────

export const fetchLoanProducts = (loan_type?: string): Promise<LoanProduct[]> =>
  apiFetch(
    "/loans/products" +
      (loan_type ? "?loan_type=" + encodeURIComponent(loan_type) : ""),
  );

export const fetchLoanProduct = (id: string): Promise<LoanProduct> =>
  apiFetch("/loans/products/" + id);

export const checkLoanEligibility = (
  data: LoanEligibilityRequest,
): Promise<LoanEligibilityResponse> =>
  apiFetch("/loans/eligibility", {
    method: "POST",
    body: JSON.stringify(data),
  });

export const applyForLoan = (
  data: LoanEligibilityRequest,
): Promise<LoanApplication> =>
  apiFetch("/loans/applications", {
    method: "POST",
    body: JSON.stringify(data),
  });

export const fetchLoanApplications = (): Promise<LoanApplication[]> =>
  apiFetch("/loans/applications");

export const fetchLoanApplication = (id: string): Promise<LoanApplication> =>
  apiFetch("/loans/applications/" + id);

// ─── Investments ───────────────────────────────────────────────────────────

export function fetchInvestmentProducts(filters?: {
  product_type?: string;
  risk_level?: string;
}): Promise<InvestmentProduct[]> {
  const params = new URLSearchParams();
  if (filters?.product_type) params.set("product_type", filters.product_type);
  if (filters?.risk_level) params.set("risk_level", filters.risk_level);
  const qs = params.toString();
  return apiFetch("/investments/products" + (qs ? "?" + qs : ""));
}

export const fetchInvestmentProduct = (id: string): Promise<InvestmentProduct> =>
  apiFetch("/investments/products/" + id);

export const fetchHoldings = (): Promise<InvestmentHolding[]> =>
  apiFetch("/investments");

export const purchaseInvestment = (
  data: InvestmentCreate,
): Promise<InvestmentHolding> =>
  apiFetch("/investments", { method: "POST", body: JSON.stringify(data) });

// ─── Insurance ─────────────────────────────────────────────────────────────

export function fetchInsuranceProducts(filters?: {
  insurance_type?: string;
  risk_level?: string;
}): Promise<InsuranceProduct[]> {
  const params = new URLSearchParams();
  if (filters?.insurance_type)
    params.set("insurance_type", filters.insurance_type);
  if (filters?.risk_level) params.set("risk_level", filters.risk_level);
  const qs = params.toString();
  return apiFetch("/insurance/products" + (qs ? "?" + qs : ""));
}

// ─── Recommendations ───────────────────────────────────────────────────────

export const fetchRecommendations = (
  product_type?: string,
): Promise<Recommendation[]> =>
  apiFetch(
    "/recommendations" +
      (product_type
        ? "?product_type=" + encodeURIComponent(product_type)
        : ""),
  );
