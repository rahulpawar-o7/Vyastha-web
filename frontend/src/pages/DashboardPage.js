// import React, { useState, useEffect } from 'react';
// import { Link } from 'react-router-dom';
// import api from '../api/client';
// import { 
//   TrendingUp, 
//   CreditCard, 
//   FileText, 
//   AlertTriangle, 
//   Plus, 
//   Clock, 
//   CheckCircle2, 
//   ArrowUpRight,
//   ArrowDownLeft,
//   Sparkles,
//   Eye
// } from 'lucide-react';
// import { toast } from 'sonner';
// import WelcomeNamaste from '../components/WelcomeNamaste';
// import { useAuth } from '../context/AuthContext';

// export default function DashboardPage() {
//   const [stats, setStats] = useState(null);
//   const [loading, setLoading] = useState(true);
//   const [showWelcome, setShowWelcome] = useState(false);
//   const { user } = useAuth();
//   const [entitlements, setEntitlements] = useState(null);
//   const [entitlementsLoading, setEntitlementsLoading] = useState(true);

//   const fetchDashboard = async () => {
//     try {
//       const res = await api.get('/dashboard/stats');
//       setStats(res.data);
//     } catch (e) {
//       toast.error('Failed to load dashboard metrics');
//     } finally {
//       setLoading(false);
//     }
//   };

// useEffect(() => {
//   fetchDashboard();
// }, []);

// useEffect(() => {
//   if (sessionStorage.getItem('vyastha_show_welcome')) {
//     setShowWelcome(true);
//     sessionStorage.removeItem('vyastha_show_welcome');
//   }
// }, []);

// useEffect(() => {
//   const fetchEntitlements = async () => {
//     try {
//       const res = await api.get('/auth/entitlements');
//       setEntitlements(res.data);
//     } catch (e) {
//       console.error('Failed to load subscription details', e);
//     } finally {
//       setEntitlementsLoading(false);
//     }
//   };

//   fetchEntitlements();
// }, []);

// const trialDays = entitlements?.trial_days ?? 0;

// const trialEnd = entitlements?.current_period_end
//   ? new Date(entitlements.current_period_end)
//   : null;

// const remainingDays = trialEnd
//   ? Math.max(
//       0,
//       Math.ceil((trialEnd - new Date()) / (1000 * 60 * 60 * 24))
//     )
//   : 0;

// const isTrial = entitlements?.status === 'trialing';

//   return (
//     <div className="space-y-6">
//       {!entitlementsLoading && entitlements && isTrial && (
//   <div className="bg-white p-5 rounded-2xl border border-blue-200 shadow-sm">
//     <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      
//       <div>
//         <p className="text-xs font-bold uppercase tracking-wider text-blue-600">
//           {entitlements.plan_name} Trial
//         </p>

//         <h3 className="mt-1 text-xl font-black text-slate-900">
//           {trialDays} days trial
//         </h3>

//         <p className="mt-1 text-sm text-slate-500">
//           {remainingDays} days remaining
//         </p>
//       </div>

//       <div className="text-right">
//         <div className="text-2xl font-black text-blue-600">
//           {remainingDays}
//         </div>
//         <p className="text-[11px] text-slate-400 uppercase font-bold">
//           Days Left
//         </p>
//       </div>

//     </div>
//   </div>
// )}
//       <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
//         <div>
//           <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight" data-testid="dashboard-title">
//             Business Overview
//           </h1>
//           <p className="text-xs sm:text-sm text-slate-500">
//             Real-time financial performance, billing status, and inventory metrics.
//           </p>
//         </div>

//         <div className="flex items-center space-x-3">
//           <Link
//             to="/invoices/new"
//             data-testid="dashboard-create-invoice-btn"
//             className="px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold uppercase tracking-wider flex items-center space-x-2 shadow-sm transition-all"
//           >
//             <Plus size={16} />
//             <span>Create Invoice</span>
//           </Link>
//           <Link
//             to="/quotations/new"
//             data-testid="dashboard-create-quote-btn"
//             className="px-4 py-2.5 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-bold uppercase tracking-wider flex items-center space-x-2 shadow-sm transition-all"
//           >
//             <Plus size={16} />
//             <span>New Quotation</span>
//           </Link>
//         </div>
//       </div>

//       <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
//         <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-2">
//           <div className="flex justify-between items-center text-slate-500">
//             <span className="text-xs font-bold uppercase tracking-wider">Total Invoiced</span>
//             <TrendingUp size={18} className="text-blue-600" />
//           </div>
//           <div className="text-2xl font-black text-slate-950 font-mono" data-testid="stat-total-revenue">
//             ₹{stats?.total_revenue?.toLocaleString('en-IN') || '0.00'}
//           </div>
//           <p className="text-[11px] text-slate-400">Lifetime billed across all clients</p>
//         </div>

//         <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-2">
//           <div className="flex justify-between items-center text-slate-500">
//             <span className="text-xs font-bold uppercase tracking-wider">Today's Collections</span>
//             <CreditCard size={18} className="text-emerald-600" />
//           </div>
//           <div className="text-2xl font-black text-emerald-600 font-mono" data-testid="stat-today-collected">
//             ₹{stats?.today_collected?.toLocaleString('en-IN') || '0.00'}
//           </div>
//           <p className="text-[11px] text-slate-400">Total payments cleared today</p>
//         </div>

//         <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-2">
//           <div className="flex justify-between items-center text-slate-500">
//             <span className="text-xs font-bold uppercase tracking-wider">Outstanding Balance</span>
//             <Clock size={18} className="text-amber-600" />
//           </div>
//           <div className="text-2xl font-black text-amber-600 font-mono" data-testid="stat-total-outstanding">
//             ₹{stats?.total_outstanding?.toLocaleString('en-IN') || '0.00'}
//           </div>
//           <p className="text-[11px] text-slate-400">{stats?.unpaid_invoices_count || 0} unpaid / pending bills</p>
//         </div>

//         <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-2">
//           <div className="flex justify-between items-center text-slate-500">
//             <span className="text-xs font-bold uppercase tracking-wider">Daily Drafts Used</span>
//             <span className="text-xs font-mono font-bold text-slate-700" data-testid="stat-drafts-count">
//               {stats?.today_drafts_count || 0}/50
//             </span>
//           </div>
//           <div className="text-lg font-bold text-slate-800">
//             {50 - (stats?.today_drafts_count || 0)} Drafts Left
//           </div>
//           <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
//             <div 
//               className="bg-blue-600 h-full"
//               style={{ width: `${Math.min(100, ((stats?.today_drafts_count || 0) / 50) * 100)}%` }}
//             />
//           </div>
//         </div>
//       </div>

//       <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
//         <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-4">
//           <div className="flex justify-between items-center border-b border-slate-100 pb-3">
//             <h3 className="font-bold text-base text-slate-900 flex items-center space-x-2">
//               <FileText size={18} className="text-blue-600" />
//               <span>Recent Invoices</span>
//             </h3>
//             <Link to="/invoices" data-testid="view-all-invoices-link" className="text-xs font-bold text-blue-600 hover:underline">
//               View All &rarr;
//             </Link>
//           </div>

//           {stats?.recent_invoices?.length > 0 ? (
//             <div className="divide-y divide-slate-100">
//               {stats.recent_invoices.map((inv) => (
//                 <div key={inv.id} className="py-3 flex justify-between items-center text-xs">
//                   <div className="space-y-0.5">
//                     <div className="flex items-center space-x-2">
//                       <span className="font-mono font-bold text-slate-900">{inv.invoice_number}</span>
//                       <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
//                         inv.payment_status === 'paid' ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'
//                       }`}>
//                         {inv.payment_status}
//                       </span>
//                     </div>
//                     <p className="text-slate-500 truncate max-w-[200px]">{inv.buyer_details?.company_name || 'Client'}</p>
//                   </div>
//                   <div className="text-right">
//                     <p className="font-mono font-bold text-slate-900">₹{inv.total_amount?.toLocaleString('en-IN')}</p>
//                     <p className="text-[10px] text-slate-400">{inv.invoice_date}</p>
//                   </div>
//                 </div>
//               ))}
//             </div>
//           ) : (
//             <div className="py-8 text-center text-slate-400 text-xs">
//               No invoices generated yet. Click "Create Invoice" to start!
//             </div>
//           )}
//         </div>

//         <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-4">
//           <div className="flex justify-between items-center border-b border-slate-100 pb-3">
//             <h3 className="font-bold text-base text-slate-900 flex items-center space-x-2">
//               <CreditCard size={18} className="text-emerald-600" />
//               <span>Recent Payment Transactions</span>
//             </h3>
//             <Link to="/payments" data-testid="view-all-payments-link" className="text-xs font-bold text-blue-600 hover:underline">
//               View All &rarr;
//             </Link>
//           </div>

//           {stats?.recent_payments?.length > 0 ? (
//             <div className="divide-y divide-slate-100">
//               {stats.recent_payments.map((p) => (
//                 <div key={p.id} className="py-3 flex justify-between items-center text-xs">
//                   <div className="space-y-0.5">
//                     <div className="flex items-center space-x-2">
//                       <span className="font-mono font-bold text-slate-900">{p.invoice_number || 'Direct Pay'}</span>
//                       <span className="px-2 py-0.5 bg-blue-50 text-blue-700 rounded text-[10px] font-mono">
//                         {p.payment_method}
//                       </span>
//                     </div>
//                     <p className="text-slate-500 truncate max-w-[200px]">{p.customer_name}</p>
//                   </div>
//                   <div className="text-right">
//                     <p className="font-mono font-bold text-emerald-600">+₹{p.amount?.toLocaleString('en-IN')}</p>
//                     <p className="text-[10px] text-slate-400 font-mono">{p.transaction_ref}</p>
//                   </div>
//                 </div>
//               ))}
//             </div>
//           ) : (
//             <div className="py-8 text-center text-slate-400 text-xs">
//               No payment transactions recorded yet.
//             </div>
//           )}
//         </div>
//       </div>
//       {showWelcome && (
//         <WelcomeNamaste
//           userName={user?.name || ''}
//           onComplete={() => setShowWelcome(false)}
//         />
//       )}
//     </div>
//   );
// }











import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../api/client';
import {
  TrendingUp,
  CreditCard,
  FileText,
  Clock,
  Plus,
  Sparkles,
  CheckCircle2,
  ArrowUpRight,
} from 'lucide-react';
import { toast } from 'sonner';
import WelcomeNamaste from '../components/WelcomeNamaste';
import { useAuth } from '../context/AuthContext';

export default function DashboardPage() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showWelcome, setShowWelcome] = useState(false);

  const { user } = useAuth();

  const [entitlements, setEntitlements] = useState(null);
  const [entitlementsLoading, setEntitlementsLoading] = useState(true);

  const fetchDashboard = async () => {
    try {
      const res = await api.get('/dashboard/stats');
      setStats(res.data);
    } catch (e) {
      toast.error('Failed to load dashboard metrics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, []);

  useEffect(() => {
    if (sessionStorage.getItem('vyastha_show_welcome')) {
      setShowWelcome(true);
      sessionStorage.removeItem('vyastha_show_welcome');
    }
  }, []);

  useEffect(() => {
    const fetchEntitlements = async () => {
      try {
        const res = await api.get('/auth/entitlements');
        setEntitlements(res.data);
      } catch (e) {
        console.error('Failed to load subscription details', e);
      } finally {
        setEntitlementsLoading(false);
      }
    };

    fetchEntitlements();
  }, []);

  /*
   * Subscription / Trial calculations
   */
  const currentPlanSlug = entitlements?.plan_slug || 'free';

  const isPro = currentPlanSlug === 'pro';
  const isTrial = entitlements?.status === 'trialing';

  const trialDays = entitlements?.trial_days ?? (isPro ? 3 : 90);

  const trialEnd = entitlements?.current_period_end
    ? new Date(entitlements.current_period_end)
    : null;

  const remainingDays = trialEnd
    ? Math.max(
        0,
        Math.ceil(
          (trialEnd - new Date()) / (1000 * 60 * 60 * 24)
        )
      )
    : 0;

  const planName = isPro ? 'Vyastha Pro' : 'Vyastha';

  /*
   * Draft limit
   */
  const draftsUsed = stats?.today_drafts_count || 0;
  const draftLimit = 50;
  const draftsLeft = Math.max(0, draftLimit - draftsUsed);
  const draftPercentage = Math.min(
    100,
    (draftsUsed / draftLimit) * 100
  );

  return (
    <div className="space-y-6">

      {/* =========================================================
          SUBSCRIPTION / TRIAL CARD
         ========================================================= */}
      {!entitlementsLoading && (
        <div
          className={`relative overflow-hidden rounded-2xl border shadow-sm ${
            isPro
              ? 'bg-slate-950 border-slate-800'
              : 'bg-white border-blue-200'
          }`}
        >
          {/* Decorative background */}
          {isPro && (
            <div className="absolute -top-20 -right-20 w-48 h-48 bg-blue-600/20 rounded-full blur-3xl" />
          )}

          <div className="relative p-5 sm:p-6">
            <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-5">

              {/* Plan Information */}
              <div className="flex items-start gap-4">

                <div
                  className={`w-11 h-11 rounded-xl flex items-center justify-center shrink-0 ${
                    isPro
                      ? 'bg-blue-600 text-white'
                      : 'bg-blue-50 text-blue-600'
                  }`}
                >
                  <Sparkles size={21} />
                </div>

                <div>
                  <div className="flex items-center gap-2 flex-wrap">
                    <p
                      className={`text-xs font-bold uppercase tracking-wider ${
                        isPro
                          ? 'text-blue-400'
                          : 'text-blue-600'
                      }`}
                    >
                      Current Plan
                    </p>

                    {isPro && (
                      <span className="px-2 py-0.5 rounded-full bg-blue-600 text-white text-[9px] font-black uppercase tracking-wider">
                        PRO
                      </span>
                    )}
                  </div>

                  <h2
                    className={`mt-1 text-xl sm:text-2xl font-black ${
                      isPro
                        ? 'text-white'
                        : 'text-slate-900'
                    }`}
                  >
                    {planName}
                  </h2>

                  <p
                    className={`mt-1 text-sm ${
                      isPro
                        ? 'text-slate-400'
                        : 'text-slate-500'
                    }`}
                  >
                    {isPro
                      ? 'Advanced Vyastha features for growing businesses.'
                      : 'Core Vyastha business management features.'}
                  </p>
                </div>
              </div>

              {/* Trial / Pricing */}
              <div
                className={`flex flex-col sm:flex-row sm:items-center gap-4 ${
                  isPro
                    ? 'text-white'
                    : 'text-slate-900'
                }`}
              >
                {isTrial ? (
                  <div
                    className={`px-4 py-3 rounded-xl border ${
                      isPro
                        ? 'bg-white/5 border-white/10'
                        : 'bg-blue-50 border-blue-100'
                    }`}
                  >
                    <p
                      className={`text-[10px] font-bold uppercase tracking-wider ${
                        isPro
                          ? 'text-blue-400'
                          : 'text-blue-600'
                      }`}
                    >
                      Free Trial
                    </p>

                    <div className="flex items-baseline gap-2 mt-1">
                      <span className="text-xl font-black">
                        {remainingDays}
                      </span>

                      <span
                        className={`text-xs ${
                          isPro
                            ? 'text-slate-400'
                            : 'text-slate-500'
                        }`}
                      >
                        {remainingDays === 1
                          ? 'day remaining'
                          : 'days remaining'}
                      </span>
                    </div>

                    <p
                      className={`text-[10px] mt-1 ${
                        isPro
                          ? 'text-slate-500'
                          : 'text-slate-400'
                      }`}
                    >
                      {trialDays} days total trial
                    </p>
                  </div>
                ) : (
                  <div
                    className={`px-4 py-3 rounded-xl border ${
                      isPro
                        ? 'bg-white/5 border-white/10'
                        : 'bg-slate-50 border-slate-200'
                    }`}
                  >
                    <p
                      className={`text-[10px] font-bold uppercase tracking-wider ${
                        isPro
                          ? 'text-slate-400'
                          : 'text-slate-500'
                      }`}
                    >
                      Monthly Plan
                    </p>

                    <div className="flex items-baseline gap-1 mt-1">
                      <span className="text-xl font-black">
                        ₹{isPro ? '99' : '49'}
                      </span>

                      <span
                        className={`text-xs ${
                          isPro
                            ? 'text-slate-400'
                            : 'text-slate-500'
                        }`}
                      >
                        /month
                      </span>
                    </div>
                  </div>
                )}

                {/* Upgrade button only for normal Vyastha */}
                {!isPro && (
                  <Link
                   to="/subscription"
                    className="px-4 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold uppercase tracking-wider flex items-center justify-center gap-2 shadow-sm transition-all"
                  >
                    <Sparkles size={15} />
                    <span>Upgrade to Pro</span>
                    <ArrowUpRight size={14} />
                  </Link>
                )}

                {/* Pro badge */}
                {isPro && (
                  <div className="px-4 py-3 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-xl text-xs font-bold flex items-center justify-center gap-2">
                    <CheckCircle2 size={15} />
                    <span>Pro Active</span>
                  </div>
                )}
              </div>
            </div>

            {/* Pro feature strip */}
            {isPro && (
              <div className="mt-5 pt-4 border-t border-white/10">
                <div className="flex flex-wrap gap-x-5 gap-y-2">
                  {[
                    'Advanced Analytics',
                    'Advanced Inventory',
                    'Smart Features',
                    'Multi-user',
                  ].map((feature) => (
                    <div
                      key={feature}
                      className="flex items-center gap-1.5 text-[11px] text-slate-300"
                    >
                      <CheckCircle2
                        size={13}
                        className="text-emerald-400"
                      />
                      <span>{feature}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* =========================================================
          PAGE HEADER
         ========================================================= */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1
            className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight"
            data-testid="dashboard-title"
          >
            Business Overview
          </h1>

          <p className="text-xs sm:text-sm text-slate-500">
            Real-time financial performance, billing status, and inventory metrics.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <Link
            to="/invoices/new"
            data-testid="dashboard-create-invoice-btn"
            className="px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold uppercase tracking-wider flex items-center space-x-2 shadow-sm transition-all"
          >
            <Plus size={16} />
            <span>Create Invoice</span>
          </Link>

          <Link
            to="/quotations/new"
            data-testid="dashboard-create-quote-btn"
            className="px-4 py-2.5 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-bold uppercase tracking-wider flex items-center space-x-2 shadow-sm transition-all"
          >
            <Plus size={16} />
            <span>New Quotation</span>
          </Link>
        </div>
      </div>

      {/* =========================================================
          MAIN STATS
         ========================================================= */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">

        {/* Total Invoiced */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-2">
          <div className="flex justify-between items-center text-slate-500">
            <span className="text-xs font-bold uppercase tracking-wider">
              Total Invoiced
            </span>

            <TrendingUp
              size={18}
              className="text-blue-600"
            />
          </div>

          <div
            className="text-2xl font-black text-slate-950 font-mono"
            data-testid="stat-total-revenue"
          >
            ₹{stats?.total_revenue?.toLocaleString('en-IN') || '0.00'}
          </div>

          <p className="text-[11px] text-slate-400">
            Lifetime billed across all clients
          </p>
        </div>

        {/* Today's Collections */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-2">
          <div className="flex justify-between items-center text-slate-500">
            <span className="text-xs font-bold uppercase tracking-wider">
              Today's Collections
            </span>

            <CreditCard
              size={18}
              className="text-emerald-600"
            />
          </div>

          <div
            className="text-2xl font-black text-emerald-600 font-mono"
            data-testid="stat-today-collected"
          >
            ₹{stats?.today_collected?.toLocaleString('en-IN') || '0.00'}
          </div>

          <p className="text-[11px] text-slate-400">
            Total payments cleared today
          </p>
        </div>

        {/* Outstanding Balance */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-2">
          <div className="flex justify-between items-center text-slate-500">
            <span className="text-xs font-bold uppercase tracking-wider">
              Outstanding Balance
            </span>

            <Clock
              size={18}
              className="text-amber-600"
            />
          </div>

          <div
            className="text-2xl font-black text-amber-600 font-mono"
            data-testid="stat-total-outstanding"
          >
            ₹{stats?.total_outstanding?.toLocaleString('en-IN') || '0.00'}
          </div>

          <p className="text-[11px] text-slate-400">
            {stats?.unpaid_invoices_count || 0} unpaid / pending bills
          </p>
        </div>

        {/* Daily Drafts */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-2">
          <div className="flex justify-between items-center text-slate-500">
            <span className="text-xs font-bold uppercase tracking-wider">
              Daily Drafts Used
            </span>

            <span
              className="text-xs font-mono font-bold text-slate-700"
              data-testid="stat-drafts-count"
            >
              {draftsUsed}/{draftLimit}
            </span>
          </div>

          <div className="text-lg font-bold text-slate-800">
            {draftsLeft} Drafts Left
          </div>

          <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
            <div
              className="bg-blue-600 h-full transition-all"
              style={{
                width: `${draftPercentage}%`,
              }}
            />
          </div>
        </div>
      </div>

      {/* =========================================================
          RECENT INVOICES + PAYMENTS
         ========================================================= */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* Recent Invoices */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-4">

          <div className="flex justify-between items-center border-b border-slate-100 pb-3">
            <h3 className="font-bold text-base text-slate-900 flex items-center space-x-2">
              <FileText
                size={18}
                className="text-blue-600"
              />

              <span>Recent Invoices</span>
            </h3>

            <Link
              to="/invoices"
              data-testid="view-all-invoices-link"
              className="text-xs font-bold text-blue-600 hover:underline"
            >
              View All &rarr;
            </Link>
          </div>

          {stats?.recent_invoices?.length > 0 ? (
            <div className="divide-y divide-slate-100">

              {stats.recent_invoices.map((inv) => (
                <div
                  key={inv.id}
                  className="py-3 flex justify-between items-center text-xs"
                >
                  <div className="space-y-0.5">

                    <div className="flex items-center space-x-2">
                      <span className="font-mono font-bold text-slate-900">
                        {inv.invoice_number}
                      </span>

                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                          inv.payment_status === 'paid'
                            ? 'bg-emerald-100 text-emerald-800'
                            : 'bg-amber-100 text-amber-800'
                        }`}
                      >
                        {inv.payment_status}
                      </span>
                    </div>

                    <p className="text-slate-500 truncate max-w-[200px]">
                      {inv.buyer_details?.company_name || 'Client'}
                    </p>
                  </div>

                  <div className="text-right">
                    <p className="font-mono font-bold text-slate-900">
                      ₹{inv.total_amount?.toLocaleString('en-IN')}
                    </p>

                    <p className="text-[10px] text-slate-400">
                      {inv.invoice_date}
                    </p>
                  </div>
                </div>
              ))}

            </div>
          ) : (
            <div className="py-8 text-center text-slate-400 text-xs">
              No invoices generated yet. Click "Create Invoice" to start!
            </div>
          )}
        </div>

        {/* Recent Payments */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-4">

          <div className="flex justify-between items-center border-b border-slate-100 pb-3">
            <h3 className="font-bold text-base text-slate-900 flex items-center space-x-2">
              <CreditCard
                size={18}
                className="text-emerald-600"
              />

              <span>Recent Payment Transactions</span>
            </h3>

            <Link
              to="/payments"
              data-testid="view-all-payments-link"
              className="text-xs font-bold text-blue-600 hover:underline"
            >
              View All &rarr;
            </Link>
          </div>

          {stats?.recent_payments?.length > 0 ? (
            <div className="divide-y divide-slate-100">

              {stats.recent_payments.map((p) => (
                <div
                  key={p.id}
                  className="py-3 flex justify-between items-center text-xs"
                >
                  <div className="space-y-0.5">

                    <div className="flex items-center space-x-2">
                      <span className="font-mono font-bold text-slate-900">
                        {p.invoice_number || 'Direct Pay'}
                      </span>

                      <span className="px-2 py-0.5 bg-blue-50 text-blue-700 rounded text-[10px] font-mono">
                        {p.payment_method}
                      </span>
                    </div>

                    <p className="text-slate-500 truncate max-w-[200px]">
                      {p.customer_name}
                    </p>
                  </div>

                  <div className="text-right">
                    <p className="font-mono font-bold text-emerald-600">
                      +₹{p.amount?.toLocaleString('en-IN')}
                    </p>

                    <p className="text-[10px] text-slate-400 font-mono">
                      {p.transaction_ref}
                    </p>
                  </div>
                </div>
              ))}

            </div>
          ) : (
            <div className="py-8 text-center text-slate-400 text-xs">
              No payment transactions recorded yet.
            </div>
          )}
        </div>
      </div>

      {/* =========================================================
          WELCOME OVERLAY
         ========================================================= */}
      {showWelcome && (
        <WelcomeNamaste
          userName={user?.name || ''}
          onComplete={() => setShowWelcome(false)}
        />
      )}

    </div>
  );
}