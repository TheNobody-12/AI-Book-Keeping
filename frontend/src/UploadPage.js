import React, { useState } from 'react';

const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:8000';

export default function UploadPage({ onExtracted }) {
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState('');

  const handleUpload = async () => {
    if (!file) return;
    setStatus('Uploading...');
    const formData = new FormData();
    formData.append('file', file);
    const up = await fetch(`${API_BASE}/upload`, { method: 'POST', body: formData });
    const upJson = await up.json();
    setStatus('Extracting...');
    const ex = await fetch(`${API_BASE}/extract/${upJson.file_id}`, { method: 'POST' });
    const exJson = await ex.json();
    setStatus('Loaded');
    onExtracted(exJson.transactions || []);
  };

  return (
    <div style={{ marginBottom: 16 }}>
      <input type="file" onChange={(e) => setFile(e.target.files?.[0] || null)} />
      <button onClick={handleUpload} disabled={!file} style={{ marginLeft: 8 }}>Upload & Extract</button>
      <span style={{ marginLeft: 8, color: '#555' }}>{status}</span>
    </div>
  );
}

