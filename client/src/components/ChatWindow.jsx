import { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import { sendMessage, getMessages, getConversations } from '../services/api';

export default function ChatWindow({
  messages,
  setMessages,
  activeConversation,
  setActiveConversation,
  conversations,
  setConversations,
  model,
}) {
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  // Load messages when conversation changes
  useEffect(() => {
    if (activeConversation) {
      loadMessages(activeConversation);
    }
  }, [activeConversation]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const loadMessages = async (convId) => {
    try {
      const msgs = await getMessages(convId);
      setMessages(msgs);
    } catch (err) {
      console.error('Failed to load messages:', err);
    }
  };

  const handleSend = async () => {
    const trimmed = input.trim();
    if (!trimmed || loading) return;

    // Add user message optimistically
    const userMsg = {
      id: Date.now().toString(),
      role: 'user',
      content: trimmed,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }

    try {
      const response = await sendMessage(trimmed, activeConversation, model);

      // Add assistant response
      const assistantMsg = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.reply,
        sources: response.sources || [],
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMsg]);

      // Update conversation ID if new
      if (!activeConversation) {
        setActiveConversation(response.conversation_id);
      }

      // Refresh conversations list
      const convs = await getConversations();
      setConversations(convs);
    } catch (err) {
      let errorText = err.response?.data?.detail || err.message || 'Something went wrong.';
      if (err.response?.status === 429) {
        errorText = '⚠️ API quota exceeded. Please update your API keys in server/.env file.';
      } else if (err.response?.status === 504) {
        errorText = '⏱️ AI service timed out. Try switching to a different model.';
      } else if (!err.response) {
        errorText = '🔌 Cannot reach the backend server. Make sure it is running on port 8003.';
      }
      const errorMsg = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: errorText,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleTextareaChange = (e) => {
    setInput(e.target.value);
    // Auto-resize textarea
    e.target.style.height = 'auto';
    e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px';
  };

  const handleSuggestion = (text) => {
    setInput(text);
    textareaRef.current?.focus();
  };

  const suggestions = [
    '📄 Summarize my uploaded documents',
    '❓ What are the key topics covered?',
    '🔍 Explain the main concepts',
    '📝 Generate study notes from my docs',
  ];

  return (
    <div className="chat-container">
      <div className="messages-area">
        {messages.length === 0 && !loading ? (
          <div className="welcome-screen">
            <div className="welcome-icon">🧠</div>
            <h2>DocuMind AI</h2>
            <p>
              Upload documents and ask questions. I use RAG (Retrieval Augmented Generation)
              to find relevant information and provide accurate, sourced answers.
            </p>
            <div className="suggestion-chips">
              {suggestions.map((s, i) => (
                <button
                  key={i}
                  className="suggestion-chip"
                  onClick={() => handleSuggestion(s)}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <>
            {messages.map((msg) => (
              <div key={msg.id} className={`message ${msg.role}`}>
                <div className="message-avatar">
                  {msg.role === 'assistant' ? '🧠' : '👤'}
                </div>
                <div className="message-body">
                  <div className="message-content">
                    {msg.role === 'assistant' ? (
                      <ReactMarkdown>{msg.content}</ReactMarkdown>
                    ) : (
                      msg.content
                    )}
                  </div>
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="sources">
                      {msg.sources.map((src, i) => (
                        <span key={i} className="source-tag">
                          📎 {src.document} ({(src.relevance * 100).toFixed(0)}%)
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {loading && (
              <div className="message assistant">
                <div className="message-avatar">🧠</div>
                <div className="message-body">
                  <div className="message-content">
                    <div className="typing-indicator">
                      <div className="typing-dot"></div>
                      <div className="typing-dot"></div>
                      <div className="typing-dot"></div>
                    </div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      <div className="chat-input-area">
        <div className="chat-input-wrapper">
          <textarea
            ref={textareaRef}
            className="chat-input"
            placeholder="Ask anything about your documents..."
            value={input}
            onChange={handleTextareaChange}
            onKeyDown={handleKeyDown}
            rows={1}
          />
          <button
            className="send-btn"
            onClick={handleSend}
            disabled={!input.trim() || loading}
            title="Send message"
          >
            ▶
          </button>
        </div>
      </div>
    </div>
  );
}
