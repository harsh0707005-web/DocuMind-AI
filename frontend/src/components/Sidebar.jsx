import { useEffect } from 'react';
import { ArrowRight, BrainCircuit, MessageSquareText, Plus, Trash2 } from 'lucide-react';
import { getConversations, deleteConversation } from '../services/api';

export default function Sidebar({
  conversations,
  setConversations,
  activeConversation,
  setActiveConversation,
  setMessages,
  sidebarOpen,
}) {
  useEffect(() => {
    loadConversations();
  }, []);

  const loadConversations = async () => {
    try {
      const convs = await getConversations();
      setConversations(convs);
    } catch (err) {
      console.error('Failed to load conversations:', err);
    }
  };

  const handleNewChat = () => {
    setActiveConversation(null);
    setMessages([]);
  };

  const handleDeleteConversation = async (e, convId) => {
    e.stopPropagation();
    try {
      await deleteConversation(convId);
      setConversations((prev) => prev.filter((c) => c.id !== convId));
      if (activeConversation === convId) {
        setActiveConversation(null);
        setMessages([]);
      }
    } catch (err) {
      console.error('Failed to delete conversation:', err);
    }
  };

  return (
    <aside className={`sidebar ${sidebarOpen ? '' : 'closed'}`}>
      <div className="sidebar-header">
        <div className="logo">
          <BrainCircuit size={18} />
        </div>
        <div>
          <div className="sidebar-kicker">Creative AI workspace</div>
          <h1>DocuMind AI</h1>
        </div>
      </div>

      <div className="sidebar-hero">
        <p className="sidebar-hero-label">Atmospheric workspace</p>
        <h2>Turn documents into conversation, structure, and recall.</h2>
        <p className="sidebar-hero-copy">
          A more immersive command deck for chatting with sources, curating files, and generating study assets.
        </p>
      </div>

      <button className="new-chat-btn" onClick={handleNewChat}>
        <Plus size={16} />
        New Orbit
      </button>

      <div className="conversations-list">
        {conversations.length > 0 && <div className="conv-label">Conversation Dock</div>}

        {conversations.map((conv) => (
          <div
            key={conv.id}
            className={`conv-item ${activeConversation === conv.id ? 'active' : ''}`}
            onClick={() => setActiveConversation(conv.id)}
          >
            <div className="conv-item-left">
              <span className="conv-item-icon">
                <MessageSquareText size={15} />
              </span>
              <span className="conv-title">{conv.title}</span>
            </div>
            <button
              className="conv-delete-btn"
              onClick={(e) => handleDeleteConversation(e, conv.id)}
              title="Delete conversation"
            >
              <Trash2 size={14} />
            </button>
          </div>
        ))}

        {conversations.length === 0 && (
          <div className="sidebar-empty">
            <p>No conversations saved yet.</p>
            <span>Start a new orbit and your threads will appear here.</span>
            <ArrowRight size={16} />
          </div>
        )}
      </div>
    </aside>
  );
}
