import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../api/client';


import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';

import {
  TrendingUp,
  Lock,
  Loader2,
} from 'lucide-react';

const COLORS = [
  '#16A34A',
  '#CA8A04',
  '#DC2626',
  '#2563EB',
];

export default function AnalyticsPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [locked, setLocked] = useState(false);



  useEffect(() => {
    api
      .get('/analytics/advanced')
      .then((response) => {
        const backendData = response.data || {};

        /*
         * Convert current Vyastha backend response
         * into the same structure used by the authentic
         * Vyastha Pro Analytics frontend.
         */

        const monthlyRevenue =
          backendData.trends?.monthly_revenue || {};

        const monthlyCollections =
          backendData.trends?.monthly_collections || {};

        const months = Array.from(
          new Set([
            ...Object.keys(monthlyRevenue),
            ...Object.keys(monthlyCollections),
          ])
        ).sort();

        const monthly = months
          .slice(-6)
          .map((month) => ({
            month,
            sales: Number(monthlyRevenue[month] || 0),
            collected: Number(monthlyCollections[month] || 0),
          }));

        const paymentBreakdown = [
          {
            name: 'Paid',
            value: Number(
              backendData.invoices?.paid || 0
            ),
          },
          {
            name: 'Partially Paid',
            value: Number(
              backendData.invoices?.partially_paid || 0
            ),
          },
          {
            name: 'Unpaid',
            value: Number(
              backendData.invoices?.unpaid || 0
            ),
          },
        ].filter((item) => item.value > 0);

        setData({
          totals: {
            total_sales: Number(
              backendData.revenue?.total_revenue || 0
            ),
            total_collected: Number(
              backendData.revenue?.total_collected || 0
            ),
            outstanding: Number(
              backendData.revenue?.total_outstanding || 0
            ),
            invoice_count: Number(
              backendData.invoices?.active || 0
            ),
          },

          monthly,

          /*
           * Top products will be connected to the backend
           * in the next backend step.
           */
          top_products: backendData.top_products || [],

          payment_breakdown: paymentBreakdown,
        });
      })
      .catch((error) => {
        if (error.response?.status === 402) {
          setLocked(true);
        }
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="py-20 text-center text-slate-500">
        <Loader2
          className="animate-spin mx-auto"
          size={24}
        />
      </div>
    );
  }

  if (locked) {
    return (
      <div className="max-w-lg mx-auto text-center py-16 space-y-4">
        <div className="mx-auto h-16 w-16 rounded-2xl bg-blue-100 flex items-center justify-center">
          <Lock
            className="text-blue-600"
            size={28}
          />
        </div>

        <h1 className="text-2xl font-extrabold text-slate-900">
          Advanced Analytics
        </h1>

        <p className="text-slate-500">
          Upgrade to Vyastha Pro to view sales and payment trends.
        </p>

        <Link
          to="/subscription"
          data-testid="analytics-upgrade-btn"
          className="inline-block px-5 py-2.5 bg-blue-600 text-white rounded-xl font-bold text-sm"
        >
          View Plans
        </Link>
      </div>
    );
  }

  const totals = data?.totals || {};

  return (
    <div
      className="space-y-6"
      data-testid="analytics-page"
    >
      {/* Header */}
      <div>
        <h1
          className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight"
          data-testid="analytics-title"
        >
          Business Analytics
        </h1>

        <p className="text-sm text-slate-500">
          Sales aur payment trends — last 6 months.
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          {
            label: 'Total Sales',
           value: `₹${Number(totals.total_sales || 0).toLocaleString('en-IN')}`,
            color: 'text-blue-600',
          },
          {
            label: 'Collected',
           value: `₹${Number(totals.total_collected || 0).toLocaleString('en-IN')}`,
            color: 'text-emerald-600',
          },
          {
            label: 'Outstanding',
            value: `₹${Number(totals.outstanding || 0).toLocaleString('en-IN')}`,
            color: 'text-amber-600',
          },
          {
            label: 'Invoices',
            value: totals.invoice_count || 0,
            color: 'text-slate-900',
          },
        ].map((card) => (
          <div
            key={card.label}
            className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm"
          >
            <p className="text-xs font-bold uppercase tracking-wider text-slate-500">
              {card.label}
            </p>

            <p
              className={`text-xl font-black font-mono ${card.color}`}
            >
              {card.value}
            </p>
          </div>
        ))}
      </div>

      {/* Sales vs Collections */}
      <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
        <h3 className="font-bold text-slate-900 mb-4 flex items-center gap-2">
          <TrendingUp
            size={18}
            className="text-blue-600"
          />

          Sales vs Collections
        </h3>

        <ResponsiveContainer
          width="100%"
          height={280}
        >
          <AreaChart data={data?.monthly || []}>
            <defs>
              <linearGradient
                id="gS"
                x1="0"
                y1="0"
                x2="0"
                y2="1"
              >
                <stop
                  offset="5%"
                  stopColor="#2563EB"
                  stopOpacity={0.3}
                />

                <stop
                  offset="95%"
                  stopColor="#2563EB"
                  stopOpacity={0}
                />
              </linearGradient>

              <linearGradient
                id="gC"
                x1="0"
                y1="0"
                x2="0"
                y2="1"
              >
                <stop
                  offset="5%"
                  stopColor="#16A34A"
                  stopOpacity={0.3}
                />

                <stop
                  offset="95%"
                  stopColor="#16A34A"
                  stopOpacity={0}
                />
              </linearGradient>
            </defs>

            <CartesianGrid
              strokeDasharray="3 3"
              stroke="#E2E8F0"
            />

            <XAxis
              dataKey="month"
              tick={{ fontSize: 12 }}
            />

            <YAxis
                tickFormatter={(value) =>
                    `₹${Number(value || 0).toLocaleString('en-IN')}`
                }
                tick={{ fontSize: 11 }}
                width={70}
            />

            <Tooltip
              formatter={(value) =>
                `₹${Number(value || 0).toLocaleString('en-IN')}`
              }
            />

            <Legend />

            <Area
              type="monotone"
              dataKey="sales"
              name="Sales"
              stroke="#2563EB"
              fill="url(#gS)"
              strokeWidth={2}
            />

            <Area
              type="monotone"
              dataKey="collected"
              name="Collected"
              stroke="#16A34A"
              fill="url(#gC)"
              strokeWidth={2}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Bottom Sections */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* Top Products */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
          <h3 className="font-bold text-slate-900 mb-4">
            Top Products by Revenue
          </h3>

          {data?.top_products?.length ? (
            <ResponsiveContainer
              width="100%"
              height={260}
            >
              <BarChart
                data={data.top_products}
                layout="vertical"
                margin={{ left: 10 }}
              >
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="#E2E8F0"
                />

               <XAxis
                    type="number"
                    tickFormatter={(value) =>
                        `₹${Number(value || 0).toLocaleString('en-IN')}`
                    }
                    tick={{ fontSize: 11 }}
                />

                <YAxis
                  type="category"
                  dataKey="product_name"
                  width={110}
                  tick={{ fontSize: 11 }}
                />

                <Tooltip
                  formatter={(value) =>
                    `₹${Number(value || 0).toLocaleString('en-IN')}`
                  }
                />

                <Bar
                  dataKey="revenue"
                  name="Revenue"
                  fill="#2563EB"
                  radius={[0, 6, 6, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[260px] flex items-center justify-center text-sm text-slate-400">
              Product revenue data will appear here.
            </div>
          )}
        </div>

        {/* Invoice Payment Status */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
          <h3 className="font-bold text-slate-900 mb-4">
            Invoice Payment Status
          </h3>

          {data?.payment_breakdown?.length ? (
            <ResponsiveContainer
              width="100%"
              height={260}
            >
              <PieChart>
                <Pie
                  data={data.payment_breakdown}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={90}
                  label
                >
                  {data.payment_breakdown.map(
                    (entry, index) => (
                      <Cell
                        key={index}
                        fill={
                          COLORS[
                            index % COLORS.length
                          ]
                        }
                      />
                    )
                  )}
                </Pie>

                <Tooltip />

                <Legend />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[260px] flex items-center justify-center text-sm text-slate-400">
              No invoice payment data available.
            </div>
          )}
        </div>

      </div>
    </div>
  );
}