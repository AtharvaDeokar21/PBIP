"use client";
/**
 * React hooks for every customer API resource.
 * Each hook returns { data, loading, error, refresh }.
 * Used to progressively replace sample-data in customer-pages.tsx.
 */
import { useCallback, useEffect, useState } from "react";
import {
  fetchSummary,
  fetchProfile,
  updateProfile,
  fetchAccounts,
  fetchTransactions,
  fetchPayees,
  createPayee,
  updatePayee,
  deletePayee,
  createTransfer,
  fetchTransfers,
  cancelTransfer,
  fetchBillers,
  payBill,
  fetchBillHistory,
  fetchLoanProducts,
  checkLoanEligibility,
  applyForLoan,
  fetchLoanApplications,
  fetchInvestmentProducts,
  fetchHoldings,
  purchaseInvestment,
  fetchInsuranceProducts,
  fetchRecommendations,
  type CustomerSummary,
  type CustomerProfile,
  type CustomerUpdate,
  type Account,
  type AccountListResponse,
  type Transaction,
  type TransactionFilters,
  type Page,
  type Payee,
  type PayeeCreate,
  type PayeeUpdate,
  type Transfer,
  type TransferCreate,
  type Biller,
  type BillPaymentCreate,
  type BillPayment,
  type LoanProduct,
  type LoanEligibilityRequest,
  type LoanEligibilityResponse,
  type LoanApplication,
  type InvestmentProduct,
  type InvestmentHolding,
  type InvestmentCreate,
  type InsuranceProduct,
  type Recommendation,
} from "@/lib/customer/api";

// ─── Generic hook factory ─────────────────────────────────────────────────────
function useApiData<T>(fetcher: () => Promise<T>) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [rev, setRev] = useState(0);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    setError("");
    fetcher()
      .then((d) => { if (alive) setData(d); })
      .catch((e: unknown) => {
        if (alive)
          setError(
            e instanceof Error ? e.message : "Failed to load data. Please retry.",
          );
      })
      .finally(() => { if (alive) setLoading(false); });
    return () => { alive = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rev]);

  const refresh = useCallback(() => setRev((r) => r + 1), []);
  return { data, loading, error, refresh, setData };
}

// ─── Dashboard / Summary ──────────────────────────────────────────────────────
export function useCustomerSummary() {
  return useApiData<CustomerSummary>(fetchSummary);
}

// ─── Profile ─────────────────────────────────────────────────────────────────
export function useCustomerProfile() {
  return useApiData<CustomerProfile>(fetchProfile);
}

export async function saveProfile(data: CustomerUpdate): Promise<CustomerProfile> {
  return updateProfile(data);
}

// ─── Accounts ─────────────────────────────────────────────────────────────────
export function useAccounts() {
  return useApiData<AccountListResponse>(fetchAccounts);
}

// ─── Transactions ─────────────────────────────────────────────────────────────
export function useTransactions(
  accountId: string | null,
  filters: TransactionFilters = {},
) {
  const key = accountId + JSON.stringify(filters);
  const [data, setData] = useState<Page<Transaction> | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [rev, setRev] = useState(0);

  useEffect(() => {
    if (!accountId) {
      setData(null);
      setLoading(false);
      return;
    }
    let alive = true;
    setLoading(true);
    setError("");
    fetchTransactions(accountId, filters)
      .then((d) => { if (alive) setData(d); })
      .catch((e: unknown) => {
        if (alive)
          setError(
            e instanceof Error ? e.message : "Failed to load transactions.",
          );
      })
      .finally(() => { if (alive) setLoading(false); });
    return () => { alive = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [accountId, key, rev]);

  const refresh = useCallback(() => setRev((r) => r + 1), []);
  return { data, loading, error, refresh };
}

// ─── Payees ───────────────────────────────────────────────────────────────────
export function usePayees() {
  const result = useApiData<Payee[]>(fetchPayees);

  async function addPayee(d: PayeeCreate) {
    const p = await createPayee(d);
    result.setData((prev) => (prev ? [p, ...prev] : [p]));
    return p;
  }

  async function editPayee(id: string, d: PayeeUpdate) {
    const p = await updatePayee(id, d);
    result.setData((prev) =>
      prev ? prev.map((x) => (x.id === id ? p : x)) : [p],
    );
    return p;
  }

  async function removePayee(id: string) {
    await deletePayee(id);
    result.setData((prev) =>
      prev ? prev.filter((x) => x.id !== id) : [],
    );
  }

  return { ...result, addPayee, editPayee, removePayee };
}

// ─── Transfers ────────────────────────────────────────────────────────────────
export function useTransfers(page = 1, pageSize = 20, status?: string) {
  return useApiData<Page<Transfer>>(() =>
    fetchTransfers(page, pageSize, status),
  );
}

export async function submitTransfer(d: TransferCreate): Promise<Transfer> {
  return createTransfer(d);
}

export async function cancelATransfer(id: string): Promise<Transfer> {
  return cancelTransfer(id);
}

// ─── Bills ────────────────────────────────────────────────────────────────────
export function useBillers(category?: string) {
  return useApiData<Biller[]>(() => fetchBillers(category));
}

export function useBillHistory(page = 1, pageSize = 20) {
  return useApiData<Page<BillPayment>>(() => fetchBillHistory(page, pageSize));
}

export async function submitBillPayment(d: BillPaymentCreate): Promise<BillPayment> {
  return payBill(d);
}

// ─── Loans ────────────────────────────────────────────────────────────────────
export function useLoanProducts(loanType?: string) {
  return useApiData<LoanProduct[]>(() => fetchLoanProducts(loanType));
}

export function useLoanApplications() {
  return useApiData<LoanApplication[]>(fetchLoanApplications);
}

export async function checkEligibility(
  d: LoanEligibilityRequest,
): Promise<LoanEligibilityResponse> {
  return checkLoanEligibility(d);
}

export async function submitLoanApplication(
  d: LoanEligibilityRequest,
): Promise<LoanApplication> {
  return applyForLoan(d);
}

// ─── Investments ──────────────────────────────────────────────────────────────
export function useInvestmentProducts(filters?: {
  product_type?: string;
  risk_level?: string;
}) {
  return useApiData<InvestmentProduct[]>(() => fetchInvestmentProducts(filters));
}

export function useHoldings() {
  return useApiData<InvestmentHolding[]>(fetchHoldings);
}

export async function buyInvestment(d: InvestmentCreate): Promise<InvestmentHolding> {
  return purchaseInvestment(d);
}

// ─── Insurance ────────────────────────────────────────────────────────────────
export function useInsuranceProducts(filters?: {
  insurance_type?: string;
  risk_level?: string;
}) {
  return useApiData<InsuranceProduct[]>(() => fetchInsuranceProducts(filters));
}

// ─── Recommendations ──────────────────────────────────────────────────────────
export function useRecommendations(productType?: string) {
  return useApiData<Recommendation[]>(() => fetchRecommendations(productType));
}

// ─── Re-exports for convenience ───────────────────────────────────────────────
export type {
  CustomerSummary,
  CustomerProfile,
  CustomerUpdate,
  Account,
  AccountListResponse,
  Transaction,
  TransactionFilters,
  Page,
  Payee,
  PayeeCreate,
  PayeeUpdate,
  Transfer,
  TransferCreate,
  Biller,
  BillPaymentCreate,
  BillPayment,
  LoanProduct,
  LoanEligibilityRequest,
  LoanEligibilityResponse,
  LoanApplication,
  InvestmentProduct,
  InvestmentHolding,
  InvestmentCreate,
  InsuranceProduct,
  Recommendation,
};
