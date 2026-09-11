import React, { useMemo, useState } from "react";
import "./invoice.css";

export type InvoiceItem = {
  product_id?: string;
  name: string;
  hsn_sac?: string;
  quantity: number;
  unit?: string;
  price_per_unit: number;
  discount?: number;
  gst_rate: number;
};

export type BillingData = {
  business: {
    name: string; address?: string; phone?: string; email?: string;
    gstin?: string; state?: string; state_code?: string; logo_url?: string;
    bank_details?: string; upi_id?: string; payment_terms?: string;
    footer_note?: string; authorized_signatory?: string;
  };
  customer?: {
    name?: string; phone?: string; address?: string;
    gstin?: string; state?: string; state_code?: string;
  };
  items: InvoiceItem[];
  invoice_number?: string;
  invoice_date?: string;
  amount_received?: number;
  payment_terms?: string;
  notes?: string;
};

type Props = {
  billingData: BillingData;
  apiBase?: string;
  onSaved?: (invoice: any) => void;
};

const money = (n: number) =>
  new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR" }).format(n);

function isIntraState(data: BillingData) {
  return !!data.business.state_code &&
    !!data.customer?.state_code &&
    data.business.state_code === data.customer.state_code;
}

function calculate(data: BillingData) {
  const intra = isIntraState(data);
  let subtotal = 0, discount = 0, taxable = 0, cgst = 0, sgst = 0, igst = 0;

  const items = data.items.map((x, i) => {
    const gross = x.quantity * x.price_per_unit;
    const d = Math.min(x.discount || 0, gross);
    const tx = gross - d;
    const tax = tx * x.gst_rate / 100;
    const c = intra ? tax / 2 : 0;
    const s = intra ? tax / 2 : 0;
    const g = intra ? 0 : tax;
    const final = tx + tax;
    subtotal += gross; discount += d; taxable += tx;
    cgst += c; sgst += s; igst += g;
    return { ...x, index: i + 1, gross, discount: d, taxable: tx, cgst: c, sgst: s, igst: g, final };
  });

  const totalTax = cgst + sgst + igst;
  const grandTotal = taxable + totalTax;
  const received = Math.min(data.amount_received || 0, grandTotal);
  return {
    items, subtotal, discount, taxable, cgst, sgst, igst,
    totalTax, grandTotal, received, balance: grandTotal - received,
    intra,
  };
}

const fmtDate = (d?: string) =>
  d ? new Date(d).toLocaleDateString("en-IN") : new Date().toLocaleDateString("en-IN");

function Classic({ data, calc }: { data: BillingData; calc: any }) {
  return <div className="invoice-paper">
    <div className="inv-top">
      <div className="business">
        {data.business.logo_url && <img src={data.business.logo_url} className="logo" />}
        <h1>{data.business.name}</h1>
        <div>{data.business.address}</div>
        <div>{data.business.phone} {data.business.email && `• ${data.business.email}`}</div>
        {data.business.gstin && <div><b>GSTIN:</b> {data.business.gstin}</div>}
        <div>{data.business.state} {data.business.state_code && `(${data.business.state_code})`}</div>
      </div>
      <div className="invoice-meta">
        <div className="tax-title">TAX INVOICE</div>
        <div><b>Invoice No.</b><span>{data.invoice_number || "DRAFT"}</span></div>
        <div><b>Invoice Date</b><span>{fmtDate(data.invoice_date)}</span></div>
      </div>
    </div>

    <div className="billto">
      <div>
        <label>Bill To</label>
        <strong>{data.customer?.name || "Walk-in Customer"}</strong>
        <span>{data.customer?.address}</span>
        <span>{data.customer?.phone}</span>
        {data.customer?.gstin && <span>GSTIN: {data.customer.gstin}</span>}
        <span>{data.customer?.state} {data.customer?.state_code && `(${data.customer.state_code})`}</span>
      </div>
      <div className="place">
        <b>Supply Type</b>
        <span>{calc.intra ? "Intra-State — CGST + SGST" : "Inter-State — IGST"}</span>
      </div>
    </div>

    <table className="items">
      <thead><tr>
        <th>S.No.</th><th>Item Name</th><th>HSN/SAC</th><th>Qty</th><th>Unit</th>
        <th>Price/Unit</th><th>Discount</th><th>GST</th><th>Taxable</th><th>Final</th>
      </tr></thead>
      <tbody>
        {calc.items.map((x: any) => <tr key={x.index}>
          <td>{x.index}</td><td className="left">{x.name}</td><td>{x.hsn_sac || "-"}</td>
          <td>{x.quantity}</td><td>{x.unit || "pcs"}</td><td>{money(x.price_per_unit)}</td>
          <td>{money(x.discount)}</td><td>{x.gst_rate}%</td>
          <td>{money(x.taxable)}</td><td>{money(x.final)}</td>
        </tr>)}
      </tbody>
    </table>

    <div className="lower-grid">
      <div>
        <h3>Tax Breakup</h3>
        <table className="tax">
          <thead><tr><th>HSN/SAC</th><th>Taxable</th><th>CGST</th><th>SGST</th><th>IGST</th><th>Total Tax</th></tr></thead>
          <tbody>
            {calc.items.reduce((a: any[], x: any) => {
              const k = x.hsn_sac || "N/A";
              let row = a.find(r => r.k === k);
              if (!row) { row = {k, taxable:0,cgst:0,sgst:0,igst:0,tax:0}; a.push(row); }
              row.taxable += x.taxable; row.cgst += x.cgst; row.sgst += x.sgst; row.igst += x.igst;
              row.tax += x.cgst+x.sgst+x.igst; return a;
            }, []).map((r: any) => <tr key={r.k}>
              <td>{r.k}</td><td>{money(r.taxable)}</td><td>{money(r.cgst)}</td>
              <td>{money(r.sgst)}</td><td>{money(r.igst)}</td><td>{money(r.tax)}</td>
            </tr>)}
          </tbody>
        </table>
      </div>
      <div className="summary">
        <div><span>Sub Total</span><b>{money(calc.subtotal)}</b></div>
        <div><span>Total Discount</span><b>- {money(calc.discount)}</b></div>
        <div><span>CGST</span><b>{money(calc.cgst)}</b></div>
        <div><span>SGST</span><b>{money(calc.sgst)}</b></div>
        <div><span>IGST</span><b>{money(calc.igst)}</b></div>
        <div><span>Total Tax</span><b>{money(calc.totalTax)}</b></div>
        <div className="grand"><span>Grand Total</span><b>{money(calc.grandTotal)}</b></div>
        <div><span>Amount Received</span><b>{money(calc.received)}</b></div>
        <div className="due"><span>Balance Due</span><b>{money(calc.balance)}</b></div>
        <div><span>Total Savings</span><b>{money(calc.discount)}</b></div>
      </div>
    </div>

    <div className="amount-words"><b>Amount in Words:</b> {money(calc.grandTotal).replace("₹","INR ")} — {data.business.name}</div>
    <div className="footer-grid">
      <div>
        <b>Payment Terms</b><p>{data.payment_terms || data.business.payment_terms || "Due on receipt"}</p>
        <b>Notes</b><p>{data.notes || data.business.footer_note || "-"}</p>
        {data.business.bank_details && <><b>Bank / Payment Details</b><p className="pre">{data.business.bank_details}</p></>}
        {data.business.upi_id && <p><b>UPI:</b> {data.business.upi_id}</p>}
      </div>
      <div className="sign">
        <div>Authorized Signatory</div>
        <div className="sign-space"></div>
        <b>For: {data.business.name}</b>
        <div>{data.business.authorized_signatory || ""}</div>
      </div>
    </div>
  </div>;
}

function SimpleTemplate({ data, calc, premium=false }: { data: BillingData; calc: any; premium?: boolean }) {
  return <div className={`invoice-paper ${premium ? "premium" : "retail"}`}>
    <div className="simple-head">
      <div><h1>{data.business.name}</h1><p>{data.business.address}</p><p>{data.business.phone} {data.business.email}</p><p>{data.business.gstin && `GSTIN: ${data.business.gstin}`}</p></div>
      <div><div className="tax-title">TAX INVOICE</div><b>{data.invoice_number || "DRAFT"}</b><br/>{fmtDate(data.invoice_date)}</div>
    </div>
    <div className="simple-customer"><b>Bill To:</b> {data.customer?.name || "Walk-in Customer"} · {data.customer?.phone || ""}</div>
    <table className="items"><thead><tr><th>#</th><th>Item</th><th>HSN</th><th>Qty</th><th>Rate</th><th>GST</th><th>Amount</th></tr></thead>
      <tbody>{calc.items.map((x:any)=><tr key={x.index}><td>{x.index}</td><td className="left">{x.name}</td><td>{x.hsn_sac||"-"}</td><td>{x.quantity} {x.unit||""}</td><td>{money(x.price_per_unit)}</td><td>{x.gst_rate}%</td><td>{money(x.final)}</td></tr>)}</tbody>
    </table>
    <div className="simple-total"><span>Tax: {money(calc.totalTax)}</span><strong>Total: {money(calc.grandTotal)}</strong></div>
    <div className="simple-foot"><span>Amount Received: {money(calc.received)}<br/>Balance Due: {money(calc.balance)}</span><span>For: {data.business.name}<br/><br/>Authorized Signatory</span></div>
  </div>;
}

export default function InvoiceModule({ billingData, apiBase="/api", onSaved }: Props) {
  const [template, setTemplate] = useState<"classic"|"modern"|"retail"|"premium">("classic");
  const [saved, setSaved] = useState<any>(null);
  const calc = useMemo(() => calculate(billingData), [billingData]);

  async function saveInvoice() {
    const response = await fetch(`${apiBase}/invoices`, {
      method: "POST", headers: {"Content-Type":"application/json"},
      body: JSON.stringify({...billingData, template})
    });
    if (!response.ok) throw new Error(await response.text());
    const invoice = await response.json();
    setSaved(invoice); onSaved?.(invoice);
  }

  async function duplicateInvoice() {
    if (!saved) return;
    const r = await fetch(`${apiBase}/invoices/${saved.id}/duplicate`, {method:"POST"});
    if (!r.ok) throw new Error(await r.text());
    const invoice = await r.json(); setSaved(invoice); onSaved?.(invoice);
  }

  function whatsapp() {
    const phone = (billingData.customer?.phone || "").replace(/\D/g, "");
    const text = `GST Invoice ${billingData.invoice_number || ""} from ${billingData.business.name}. Total ${money(calc.grandTotal)}.`;
    window.open(`https://wa.me/${phone}?text=${encodeURIComponent(text)}`, "_blank");
  }

  async function share() {
    const text = `GST Invoice ${billingData.invoice_number || "Draft"} — ${money(calc.grandTotal)}`;
    if (navigator.share) await navigator.share({title:"Vyastha Invoice", text});
    else await navigator.clipboard.writeText(text);
  }

  const document = template === "classic"
    ? <Classic data={billingData} calc={calc}/>
    : <SimpleTemplate data={billingData} calc={calc} premium={template==="premium"}/>;

  return <section className="invoice-module">
    <div className="invoice-toolbar">
      <div><h2>GST Tax Invoice</h2><p>Preview, save, print and share</p></div>
      <div className="template-tabs">
        {(["classic","modern","retail","premium"] as const).map(x =>
          <button className={template===x ? "active":""} onClick={()=>setTemplate(x)} key={x}>
            {x==="classic"?"Classic GST":x==="modern"?"Modern GST":x==="retail"?"Retail Invoice":"Premium Business"}
          </button>
        )}
      </div>
      <div className="invoice-actions">
        <button onClick={saveInvoice}>Save Invoice</button>
        <button onClick={()=>window.print()}>Print / PDF</button>
        <button onClick={whatsapp}>WhatsApp</button>
        <button onClick={share}>Share</button>
        <button disabled={!saved} onClick={duplicateInvoice}>Duplicate</button>
      </div>
    </div>
    {document}
  </section>;
}
