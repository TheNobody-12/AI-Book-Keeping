import React, { useState } from 'react';
import UploadPage from './UploadPage';
import TransactionsTable from './TransactionsTable';

export default function App() {
  const [transactions, setTransactions] = useState([]);

  return (
    <div style={{ padding: 16, fontFamily: 'sans-serif' }}>
      <h2>AI Book Keeping</h2>
      <UploadPage onExtracted={setTransactions} />
      <TransactionsTable rows={transactions} />
    </div>
  );
}

