import { useEffect, useState } from 'react';
import Sidebar from './components/Sidebar';
import ChatWindow from './components/ChatWindow';
import DocumentUpload from './components/DocumentUpload';
import StudyTools from './components/StudyTools';
import Header from './components/Header';
import './App.css';

function App() {
  const [activeTab, setActiveTab] = useState('chat');
  const [conversations, setConversations] = useState([]);
  const [activeConversation, setActiveConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [model, setModel] = useState('gemini');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [documents, setDocuments] = useState([]);

  // High-performance pointer glow using direct CSS variable updates via requestAnimationFrame
  // Eliminates constant React re-renders on every mouse movement
  useEffect(() => {
    let ticking = false;
    const updatePointerGlow = (event) => {
      if (!ticking) {
        requestAnimationFrame(() => {
          const x = (event.clientX / window.innerWidth) * 100;
          const y = (event.clientY / window.innerHeight) * 100;
          document.documentElement.style.setProperty('--pointer-x', `${x.toFixed(1)}%`);
          document.documentElement.style.setProperty('--pointer-y', `${y.toFixed(1)}%`);
          ticking = false;
        });
        ticking = true;
      }
    };

    window.addEventListener('pointermove', updatePointerGlow, { passive: true });

    return () => {
      window.removeEventListener('pointermove', updatePointerGlow);
    };
  }, []);

  return (
    <div className="app">
      <div className="app-background" aria-hidden="true">
        <div className="app-pointer-glow"></div>
        <div className="app-orb orb-one"></div>
        <div className="app-orb orb-two"></div>
        <div className="app-orb orb-three"></div>
        <div className="app-grid"></div>
      </div>

      <Sidebar
        conversations={conversations}
        setConversations={setConversations}
        activeConversation={activeConversation}
        setActiveConversation={setActiveConversation}
        setMessages={setMessages}
        sidebarOpen={sidebarOpen}
        setModel={setModel}
      />

      <main className={`main-content ${sidebarOpen ? '' : 'sidebar-closed'}`}>
        <Header
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          model={model}
          setModel={setModel}
          sidebarOpen={sidebarOpen}
          setSidebarOpen={setSidebarOpen}
          conversationCount={conversations.length}
          documentCount={documents.length}
          messageCount={messages.length}
        />

        <div className="content-area">
          {activeTab === 'chat' && (
            <ChatWindow
              messages={messages}
              setMessages={setMessages}
              activeConversation={activeConversation}
              setActiveConversation={setActiveConversation}
              setConversations={setConversations}
              model={model}
              setModel={setModel}
            />
          )}
          {activeTab === 'documents' && (
            <DocumentUpload documents={documents} setDocuments={setDocuments} />
          )}
          {activeTab === 'study' && <StudyTools model={model} />}
        </div>
      </main>
    </div>
  );
}

export default App;
