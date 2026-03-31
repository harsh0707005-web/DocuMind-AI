import { useEffect, useRef, useState } from 'react';
import {
  BrainCircuit,
  ChevronDown,
  Files,
  GraduationCap,
  Menu,
  PanelLeftClose,
  Sparkles,
} from 'lucide-react';

export default function Header({
  activeTab,
  setActiveTab,
  model,
  setModel,
  sidebarOpen,
  setSidebarOpen,
  conversationCount,
  documentCount,
  messageCount,
}) {
  const [modelMenuOpen, setModelMenuOpen] = useState(false);
  const modelMenuRef = useRef(null);

  const tabs = [
    { id: 'chat', label: 'Neural Chat', icon: BrainCircuit },
    { id: 'documents', label: 'Document Vault', icon: Files },
    { id: 'study', label: 'Study Lab', icon: GraduationCap },
  ];

  const models = [
    { id: 'gpt-4', label: 'GPT-4o Mini' },
    { id: 'gemini', label: 'Gemini 2.0 Flash' },
    { id: 'groq', label: 'Llama 3.3 70B' },
  ];

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (!modelMenuRef.current?.contains(event.target)) {
        setModelMenuOpen(false);
      }
    };

    const handleEscape = (event) => {
      if (event.key === 'Escape') {
        setModelMenuOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleEscape);

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEscape);
    };
  }, []);

  const activeModel = models.find((item) => item.id === model) || models[0];

  return (
    <header className="header">
      <div className="header-left">
        <button
          className="toggle-sidebar-btn"
          onClick={() => setSidebarOpen(!sidebarOpen)}
          title={sidebarOpen ? 'Close sidebar' : 'Open sidebar'}
        >
          {sidebarOpen ? <PanelLeftClose size={18} /> : <Menu size={18} />}
        </button>

        <nav className="tab-nav">
          {tabs.map((tab) => {
            const Icon = tab.icon;

            return (
              <button
                key={tab.id}
                className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
                onClick={() => setActiveTab(tab.id)}
              >
                <Icon size={16} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      <div className="header-right">
        <div className="header-stats">
          <div className="header-stat">
            <span className="header-stat-value">{conversationCount}</span>
            <span className="header-stat-label">Threads</span>
          </div>
          <div className="header-stat">
            <span className="header-stat-value">{documentCount}</span>
            <span className="header-stat-label">Docs</span>
          </div>
          <div className="header-stat">
            <span className="header-stat-value">{messageCount}</span>
            <span className="header-stat-label">Messages</span>
          </div>
        </div>

        <div className="model-shell custom-model-shell" ref={modelMenuRef}>
          <button
            className="model-trigger"
            type="button"
            onClick={() => setModelMenuOpen((prev) => !prev)}
            aria-haspopup="listbox"
            aria-expanded={modelMenuOpen}
          >
            <span className="model-trigger-left">
              <Sparkles size={15} />
              <span>{activeModel.label}</span>
            </span>
            <ChevronDown size={15} className={`model-chevron ${modelMenuOpen ? 'open' : ''}`} />
          </button>

          {modelMenuOpen && (
            <div className="model-menu" role="listbox" aria-label="Choose model">
              {models.map((item) => (
                <button
                  key={item.id}
                  className={`model-menu-item ${item.id === model ? 'active' : ''}`}
                  type="button"
                  onClick={() => {
                    setModel(item.id);
                    setModelMenuOpen(false);
                  }}
                >
                  {item.label}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
