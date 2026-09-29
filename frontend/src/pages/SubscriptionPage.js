import React, { useEffect, useState } from 'react';
import api from '../api/client';
import {
  CreditCard,
  Check,
  Sparkles,
  ArrowUpRight,
  Crown,
} from 'lucide-react';
import { toast } from 'sonner';

export default function SubscriptionPage() {
  const [entitlements, setEntitlements] = useState(null);
  const [entitlementsLoading, setEntitlementsLoading] = useState(true);

  useEffect(() => {
    const loadEntitlements = async () => {
      try {
        const response = await api.get('/auth/entitlements');
        setEntitlements(response.data);
      } catch (error) {
        console.error('Failed to load subscription details:', error);
        toast.error('Unable to load subscription details.');
      } finally {
        setEntitlementsLoading(false);
      }
    };

    loadEntitlements();
  }, []);

  if (entitlementsLoading) {
    return (
      <div className="p-6">
        <div className="text-gray-500">
          Loading subscription details...
        </div>
      </div>
    );
  }

  const currentPlanSlug = entitlements?.plan_slug || 'free';
  const isPro = currentPlanSlug === 'pro';
  const isTrial = entitlements?.status === 'trialing';

  const trialDays =
    entitlements?.trial_days ?? (isPro ? 3 : 90);

  const trialEnd = entitlements?.current_period_end
    ? new Date(entitlements.current_period_end)
    : null;

  const remainingDays = trialEnd
    ? Math.max(
        0,
        Math.ceil(
          (trialEnd - new Date()) /
            (1000 * 60 * 60 * 24)
        )
      )
    : 0;

  const currentPlanName = isPro
    ? 'Vyastha Pro'
    : 'Vyastha';

  const handleUpgrade = () => {
    toast.info(
      'Vyastha Pro upgrade will be connected with Razorpay in the next billing step.'
    );
  };

  return (
    <div className="p-6 space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">
          Subscription & Plan
        </h1>

        <p className="mt-1 text-sm text-gray-500">
          Manage your Vyastha plan, trial period and Pro features.
        </p>
      </div>

      {/* Current Plan */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-xl bg-blue-50 flex items-center justify-center">
              {isPro ? (
                <Crown className="w-6 h-6 text-blue-600" />
              ) : (
                <CreditCard className="w-6 h-6 text-blue-600" />
              )}
            </div>

            <div>
              <p className="text-sm text-gray-500">
                Current Plan
              </p>

              <h2 className="text-xl font-bold text-gray-900">
                {currentPlanName}
              </h2>

              {isTrial && (
                <p className="mt-1 text-sm text-green-600 font-medium">
                  {isPro
                    ? '3 Days Free Trial'
                    : '3 Months Free Trial'}
                </p>
              )}
            </div>
          </div>

          {isPro && (
            <span className="inline-flex items-center gap-1 rounded-full bg-purple-100 px-3 py-1 text-xs font-semibold text-purple-700">
              <Sparkles className="w-3.5 h-3.5" />
              PRO
            </span>
          )}
        </div>

        <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="rounded-lg border border-gray-200 p-4">
            <p className="text-xs text-gray-500">
              Trial Period
            </p>

            <p className="mt-1 text-lg font-semibold text-gray-900">
              {isPro ? '3 Days' : '3 Months'}
            </p>
          </div>

          <div className="rounded-lg border border-gray-200 p-4">
            <p className="text-xs text-gray-500">
              Remaining
            </p>

            <p className="mt-1 text-lg font-semibold text-gray-900">
              {isTrial
                ? `${remainingDays} days`
                : 'Trial ended'}
            </p>
          </div>

          <div className="rounded-lg border border-gray-200 p-4">
            <p className="text-xs text-gray-500">
              After Trial
            </p>

            <p className="mt-1 text-lg font-semibold text-gray-900">
              {isPro ? '₹99/month' : '₹49/month'}
            </p>
          </div>
        </div>
      </div>

      {/* Plans */}
      <div>
        <div className="mb-4">
          <h2 className="text-xl font-bold text-gray-900">
            Plans
          </h2>

          <p className="text-sm text-gray-500 mt-1">
            Choose the plan that fits your business.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Vyastha */}
          <div
            className={`bg-white rounded-xl border p-6 ${
              !isPro
                ? 'border-blue-500 ring-1 ring-blue-500'
                : 'border-gray-200'
            }`}
          >
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-xl font-bold text-gray-900">
                  Vyastha
                </h3>

                <p className="text-sm text-gray-500 mt-1">
                  Essential billing and business management.
                </p>
              </div>

              {!isPro && (
                <span className="text-xs font-semibold bg-blue-100 text-blue-700 px-3 py-1 rounded-full">
                  Current
                </span>
              )}
            </div>

            <div className="mt-6">
              <span className="text-3xl font-bold text-gray-900">
                ₹49
              </span>

              <span className="text-gray-500">
                /month
              </span>
            </div>

            <p className="mt-2 text-sm text-green-600 font-medium">
              3 months free trial
            </p>

            <div className="mt-6 space-y-3">
              <div className="flex items-center gap-2 text-sm text-gray-700">
                <Check className="w-4 h-4 text-green-600" />
                Invoices & Quotations
              </div>

              <div className="flex items-center gap-2 text-sm text-gray-700">
                <Check className="w-4 h-4 text-green-600" />
                Basic Inventory
              </div>

              <div className="flex items-center gap-2 text-sm text-gray-700">
                <Check className="w-4 h-4 text-green-600" />
                Customer Management
              </div>

              <div className="flex items-center gap-2 text-sm text-gray-700">
                <Check className="w-4 h-4 text-green-600" />
                Basic Business Management
              </div>
            </div>
          </div>

          {/* Vyastha Pro */}
          <div
            className={`bg-white rounded-xl border p-6 relative overflow-hidden ${
              isPro
                ? 'border-purple-500 ring-1 ring-purple-500'
                : 'border-gray-200'
            }`}
          >
            <div className="absolute top-0 right-0">
              <div className="bg-purple-600 text-white text-xs font-semibold px-4 py-1 rounded-bl-lg">
                PRO
              </div>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-xl font-bold text-gray-900">
                  Vyastha Pro
                </h3>

                <p className="text-sm text-gray-500 mt-1">
                  Advanced tools for growing businesses.
                </p>
              </div>

              {isPro && (
                <span className="text-xs font-semibold bg-purple-100 text-purple-700 px-3 py-1 rounded-full">
                  Current
                </span>
              )}
            </div>

            <div className="mt-6">
              <span className="text-3xl font-bold text-gray-900">
                ₹99
              </span>

              <span className="text-gray-500">
                /month
              </span>
            </div>

            <p className="mt-2 text-sm text-green-600 font-medium">
              3 days free trial
            </p>

            <div className="mt-6 space-y-3">
              <div className="flex items-center gap-2 text-sm text-gray-700">
                <Check className="w-4 h-4 text-green-600" />
                Vyastha AI Business Assistant
              </div>

              <div className="flex items-center gap-2 text-sm text-gray-700">
                <Check className="w-4 h-4 text-green-600" />
                Advanced Business Analytics
              </div>

              <div className="flex items-center gap-2 text-sm text-gray-700">
                <Check className="w-4 h-4 text-green-600" />
                Smart Inventory & Low-Stock Alerts
              </div>

              <div className="flex items-center gap-2 text-sm text-gray-700">
                <Check className="w-4 h-4 text-green-600" />
                Payment & Due Management
              </div>

              <div className="flex items-center gap-2 text-sm text-gray-700">
                <Check className="w-4 h-4 text-green-600" />
                Team & Staff Management
              </div>

              <div className="flex items-center gap-2 text-sm text-gray-700">
                <Check className="w-4 h-4 text-green-600" />
                WhatsApp Invoice Delivery
              </div>

              <div className="flex items-center gap-2 text-sm text-gray-700">
                <Check className="w-4 h-4 text-green-600" />
                Advanced Reports & Export
              </div>
            </div>

            {!isPro && (
              <button
                type="button"
                onClick={handleUpgrade}
                className="mt-6 w-full inline-flex items-center justify-center gap-2 rounded-lg bg-purple-600 px-4 py-3 text-sm font-semibold text-white hover:bg-purple-700 transition"
              >
                Upgrade to Vyastha Pro
                <ArrowUpRight className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Billing Note */}
      <div className="bg-gray-50 border border-gray-200 rounded-xl p-5">
        <div className="flex items-start gap-3">
          <CreditCard className="w-5 h-5 text-gray-500 mt-0.5" />

          <div>
            <h3 className="text-sm font-semibold text-gray-900">
              Billing
            </h3>

            <p className="mt-1 text-sm text-gray-600">
              Razorpay recurring billing will be connected in
              the next billing step.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
