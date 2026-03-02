import { useState, useEffect } from 'react';
import { getConversations, deleteConversation } from '../services/api';

export default function Sidebar({
  conversations,
  setConversations,
  activeConversation,
  setActiveConversation,
  setMessages,
  sidebarOpen,
  setSidebarOpen,
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

  const handleSelectConversation = (conv) => {
    setActiveConversation(conv.id);
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
        <div className="logo">D</div>
        <h1>DocuMind AI</h1>
      </div>

      <button className="new-chat-btn" onClick={handleNewChat}>
        ✨ New Chat
      </button>

      <div className="conversations-list">
        {conversations.length > 0 && (
          <div className="conv-label">Recent Conversations</div>
        )}
        {conversations.map((conv) => (
          <div
            key={conv.id}
            className={`conv-item ${activeConversation === conv.id ? 'active' : ''}`}
            onClick={() => handleSelectConversation(conv)}
          >
            <div className="conv-item-left">
              <span className="conv-item-icon">💬</span>
              <span className="conv-title">{conv.title}</span>
            </div>
            <button
              className="conv-delete-btn"
              onClick={(e) => handleDeleteConversation(e, conv.id)}
              title="Delete conversation"
            >
              🗑️
            </button>
          </div>
        ))}
        {conversations.length === 0 && (
          <div style={{ padding: '20px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            No conversations yet.<br />Start a new chat!
          </div>
        )}
      </div>
    </aside>
  );
}
