import { useState } from 'react';

export default function Header({ activeTab, setActiveTab, model, setModel, sidebarOpen, setSidebarOpen }) {
  const tabs = [
    { id: 'chat', label: 'Chat', icon: '💬' },
    { id: 'documents', label: 'Documents', icon: '📄' },
    { id: 'study', label: 'Study Tools', icon: '🎓' },
  ];

  return (
    <header className="header">
      <div className="header-left">
        <button
          className="toggle-sidebar-btn"
          onClick={() => setSidebarOpen(!sidebarOpen)}
          title={sidebarOpen ? 'Close sidebar' : 'Open sidebar'}
        >
          {sidebarOpen ? '◀' : '☰'}
        </button>

        <nav className="tab-nav">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
            >
              {tab.icon} <span>{tab.label}</span>
            </button>
          ))}
        </nav>
      </div>

      <div className="header-right">
        <select
          className="model-select"
          value={model}
          onChange={(e) => setModel(e.target.value)}
        >
          <option value="gpt-4">⚡ GPT-4o Mini</option>
          <option value="gemini">✨ Gemini 1.5 Flash</option>
        </select>
      </div>
    </header>
  );
}
