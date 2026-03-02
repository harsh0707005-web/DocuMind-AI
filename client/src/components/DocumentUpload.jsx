import { useState, useEffect, useCallback } from 'react';
import { uploadDocument, getDocuments, deleteDocument, deleteAllDocuments } from '../services/api';

export default function DocumentUpload({ documents, setDocuments }) {
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [dragOver, setDragOver] = useState(false);
  const [alert, setAlert] = useState(null);
  const [stats, setStats] = useState({ total: 0, totalChunks: 0 });

  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    try {
      const data = await getDocuments();
      setDocuments(data.documents);
      setStats({ total: data.total, totalChunks: data.total_chunks });
    } catch (err) {
      console.error('Failed to load documents:', err);
    }
  };

  const showAlert = (type, message) => {
    setAlert({ type, message });
    setTimeout(() => setAlert(null), 5000);
  };

  const handleUpload = async (file) => {
    if (!file) return;

    setUploading(true);
    setUploadProgress(0);

    try {
      const result = await uploadDocument(file, setUploadProgress);
      showAlert('success', `✅ "${file.name}" uploaded — ${result.chunks} chunks created`);
      await loadDocuments();
    } catch (err) {
      const msg = err.response?.data?.detail || 'Upload failed';
      showAlert('error', `❌ ${msg}`);
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  const handleFileInput = (e) => {
    const file = e.target.files[0];
    if (file) handleUpload(file);
    e.target.value = '';
  };

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) handleUpload(file);
  }, []);

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = () => setDragOver(false);

  const handleDelete = async (docId, filename) => {
    try {
      await deleteDocument(docId);
      showAlert('success', `🗑️ "${filename}" deleted`);
      await loadDocuments();
    } catch (err) {
      showAlert('error', 'Failed to delete document');
    }
  };

  const handleDeleteAll = async () => {
    if (!window.confirm('Delete all documents? This cannot be undone.')) return;
    try {
      await deleteAllDocuments();
      showAlert('success', '🗑️ All documents deleted');
      await loadDocuments();
    } catch (err) {
      showAlert('error', 'Failed to delete documents');
    }
  };

  const formatSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const getFileIcon = (type) => {
    const icons = {
      '.pdf': '📕',
      '.txt': '📄',
      '.md': '📝',
      '.py': '🐍',
      '.js': '🟡',
      '.ts': '🔷',
      '.java': '☕',
      '.cpp': '⚙️',
      '.csv': '📊',
    };
    return icons[type] || '📄';
  };

  return (
    <div className="documents-container">
      <h2>📄 Document Manager</h2>
      <p>Upload your documents to enable RAG-powered Q&A. Supported: PDF, TXT, MD, Code files</p>

      {alert && (
        <div className={`alert ${alert.type}`}>{alert.message}</div>
      )}

      {/* Stats */}
      <div className="doc-stats">
        <div className="stat-card">
          <div className="stat-value">{stats.total}</div>
          <div className="stat-label">Documents</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats.totalChunks}</div>
          <div className="stat-label">Chunks Indexed</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats.totalChunks > 0 ? '✅' : '❌'}</div>
          <div className="stat-label">RAG Ready</div>
        </div>
      </div>

      {/* Upload Zone */}
      <div
        className={`upload-zone ${dragOver ? 'drag-over' : ''}`}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => document.getElementById('file-input').click()}
      >
        <input
          id="file-input"
          type="file"
          hidden
          accept=".pdf,.txt,.py,.js,.ts,.java,.cpp,.c,.md,.csv"
          onChange={handleFileInput}
        />
        <div className="upload-icon">📤</div>
        {uploading ? (
          <>
            <h3>Uploading & Processing...</h3>
            <div className="upload-progress">
              <div className="progress-bar">
                <div className="progress-fill" style={{ width: `${uploadProgress}%` }}></div>
              </div>
            </div>
          </>
        ) : (
          <>
            <h3>Drop a file here or click to upload</h3>
            <p>PDF, TXT, Markdown, Python, JavaScript, Java, C++, CSV (Max 10MB)</p>
          </>
        )}
      </div>

      {/* Document List */}
      {documents.length > 0 && (
        <>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <h3 className="doc-section-title">Uploaded Documents</h3>
            <button
              className="generate-btn"
              onClick={handleDeleteAll}
              style={{ background: 'var(--red)', fontSize: '0.8rem', padding: '6px 14px' }}
            >
              🗑️ Delete All
            </button>
          </div>

          <div className="doc-list">
            {documents.map((doc) => (
              <div key={doc.id} className="doc-item animate-fade-in">
                <div className="doc-item-left">
                  <span className="doc-icon">{getFileIcon(doc.file_type)}</span>
                  <div className="doc-info">
                    <h4>{doc.filename}</h4>
                    <p>{formatSize(doc.size)} • {doc.chunks} chunks • {doc.uploaded_at?.split('T')[0]}</p>
                  </div>
                </div>
                <button
                  className="doc-delete-btn"
                  onClick={() => handleDelete(doc.id, doc.filename)}
                  title="Delete document"
                >
                  🗑️
                </button>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
