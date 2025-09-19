import React, { useMemo, useState } from 'react';

const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:8000';

export default function TransactionsTable({ rows }) {
  const [categorized, setCategorized] = useState([]);

  const hasRows = Array.isArray(rows) && rows.length > 0;
  const categories = useMemo(
    () => [
      'Meals & Entertainment',
      'Travel',
      'Office Supplies',
      'Software & Subscriptions',
      'Utilities',
      'Income',
      'Transfers',
      'Other',
    ],
    []
  );

  const handleCategorize = async () => {
    const res = await fetch(`${API_BASE}/categorize`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ transactions: rows, categories }),
    });
    const json = await res.json();
    setCategorized(json.results || []);
  };

  if (!hasRows) return <div>No transactions loaded yet.</div>;

  return (
    <div>
      <button onClick={handleCategorize}>AI Categorize</button>
      <table style={{ width: '100%', marginTop: 8, borderCollapse: 'collapse' }}>
        <thead>
          <tr>
            <th style={th}>Date</th>
            <th style={th}>Description</th>
            <th style={th}>Deposits</th>
            <th style={th}>Withdrawals</th>
            <th style={th}>Category</th>
            <th style={th}>Confidence</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i}>
              <td style={td}>{r.date || ''}</td>
              <td style={td}>{r.description || ''}</td>
              <td style={td}>{r.deposits ?? ''}</td>
              <td style={td}>{r.withdrawals ?? ''}</td>
              <td style={td}>{categorized[i]?.category || ''}</td>
              <td style={td}>{categorized[i]?.confidence?.toFixed?.(2) || ''}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

const th = { borderBottom: '1px solid #ccc', textAlign: 'left', padding: 8 };
const td = { borderBottom: '1px solid #eee', textAlign: 'left', padding: 8 };

