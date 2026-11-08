import React, { useState, useEffect, useRef, useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import { ArrowUpRight, AudioWaveform, BrainCircuit, Compass, Sparkles } from 'lucide-react';
import { sendMessage, getMessages, getConversations } from '../services/api';

const AVAILABLE_MODELS = [
  { id: 'gpt-4', label: 'GPT-4o Mini', badge: '⚡ OpenAI', desc: 'Fast, sharp reasoning' },
  { id: 'gemini', label: 'Gemini 2.0 Flash', badge: '✦ Google', desc: 'High-speed multi-modal' },
  { id: 'groq', label: 'Llama 3.3 70B', badge: '🚀 Groq (Free)', desc: 'Ultra-fast open weights' },
];

// Memoized message item to prevent re-parsing markdown on every keystroke
const ChatMessageItem = React.memo(function ChatMessageItem({ msg, formatTime }) {
  return (
    <div className={`message ${msg.role}`}>
      <div className="message-avatar">
        {msg.role === 'assistant' ? <BrainCircuit size={16} /> : <ArrowUpRight size={16} />}
      </div>

      <div className="message-body">
        <div className="message-meta">
          <div className="meta-left">
            <span>{msg.role === 'assistant' ? 'DocuMind' : 'You'}</span>
            {msg.role === 'assistant' && msg.model_used && (
              <span className="model-used-badge" title="AI model that generated this response">
                {msg.model_used}
              </span>
            )}
          </div>
          <span>{formatTime(msg.timestamp)}</span>
        </div>

        <div className="message-content">
          {msg.role === 'assistant' ? <ReactMarkdown>{msg.content}</ReactMarkdown> : msg.content}
        </div>

        {msg.sources && msg.sources.length > 0 && (
          <div className="sources">
            {msg.sources.map((src, i) => (
              <span key={i} className="source-tag">
                {src.document} ({(src.relevance * 100).toFixed(0)}%)
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
});

export default function ChatWindow({
  messages,
  setMessages,
  activeConversation,
  setActiveConversation,
  setConversations,
  model,
  setModel,
}) {
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  useEffect(() => {
    if (activeConversation) {
      loadMessages(activeConversation);
    }
  }, [activeConversation]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages.length, loading]);

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

    const userMsg = {
      id: Date.now().toString(),
      role: 'user',
      content: trimmed,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }

    try {
      const response = await sendMessage(trimmed, activeConversation, model);

      const assistantMsg = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.reply,
        sources: response.sources || [],
        model_used: response.model_used || model,
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, assistantMsg]);

      if (!activeConversation) {
        setActiveConversation(response.conversation_id);
      }

      const convs = await getConversations();
      setConversations(convs);
    } catch (err) {
      let errorText = err.response?.data?.detail || err.message || 'Something went wrong.';

      if (err.response?.status === 429) {
        errorText = 'API quota exceeded. Please update your API keys in backend/.env file.';
      } else if (err.response?.status === 504) {
        errorText = 'AI service timed out. Try switching to a different model.';
      } else if (!err.response) {
        errorText = 'Cannot reach the backend server. Make sure it is running on port 8003.';
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
    e.target.style.height = 'auto';
    e.target.style.height = `${Math.min(e.target.scrollHeight, 120)}px`;
  };

  const handleSuggestion = (text) => {
    setInput(text);
    textareaRef.current?.focus();
  };

  const suggestions = useMemo(() => [
    'Summarize my uploaded documents',
    'What are the key topics covered?',
    'Explain the main concepts',
    'Generate study notes from my docs',
  ], []);

  const formatTime = (timestamp) =>
    new Date(timestamp).toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
    });

  return (
    <div className="chat-container">
      <div className="messages-area">
        {messages.length === 0 && !loading ? (
          <div className="welcome-screen">
            <div className="welcome-badge">
              <Sparkles size={14} />
              Retrieval-first intelligence
            </div>

            <div className="welcome-icon">
              <BrainCircuit size={42} />
            </div>

            <h2>Ask like a researcher. Explore like a futurist.</h2>
            <p>
              DocuMind blends retrieval, source awareness, and study generation into a fast, immersive knowledge
              cockpit built for dense documents and rapid insight.
            </p>

            <div className="welcome-metrics">
              <div className="welcome-metric">
                <Compass size={15} />
                Source-grounded
              </div>
              <div className="welcome-metric">
                <AudioWaveform size={15} />
                Multi-model
              </div>
              <div className="welcome-metric">
                <ArrowUpRight size={15} />
                Study-ready
              </div>
            </div>

            <div className="suggestion-chips">
              {suggestions.map((s, i) => (
                <button key={i} className="suggestion-chip" onClick={() => handleSuggestion(s)}>
                  <span>Prompt</span>
                  {s}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <>
            {messages.map((msg) => (
              <ChatMessageItem key={msg.id} msg={msg} formatTime={formatTime} />
            ))}

            {loading && (
              <div className="message assistant">
                <div className="message-avatar">
                  <BrainCircuit size={16} />
                </div>
                <div className="message-body">
                  <div className="message-meta">
                    <div className="meta-left">
                      <span>DocuMind</span>
                      <span className="model-used-badge thinking">Thinking</span>
                    </div>
                  </div>
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
        {/* Direct In-Chat Model Selector */}
        <div className="chat-model-bar">
          <div className="chat-model-label">
            <Sparkles size={13} />
            <span>AI Model:</span>
          </div>
          <div className="chat-model-options">
            {AVAILABLE_MODELS.map((m) => (
              <button
                key={m.id}
                type="button"
                className={`chat-model-pill ${model === m.id ? 'active' : ''}`}
                onClick={() => setModel(m.id)}
                title={`${m.label} — ${m.desc}`}
              >
                <span className="pill-badge">{m.badge}</span>
                <span className="pill-name">{m.label}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="chat-input-wrapper">
          <div className="chat-input-accent"></div>
          <textarea
            ref={textareaRef}
            className="chat-input"
            placeholder="Ask anything about your documents, concepts, or study material..."
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
            <ArrowUpRight size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}
