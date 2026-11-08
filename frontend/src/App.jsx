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
  const [model, setModel] = useState('gpt-4');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [documents, setDocuments] = useState([]);
  const [pointerGlow, setPointerGlow] = useState({ x: 50, y: 22 });

  useEffect(() => {
    const updatePointerGlow = (event) => {
      const x = (event.clientX / window.innerWidth) * 100;
      const y = (event.clientY / window.innerHeight) * 100;
      setPointerGlow({ x, y });
    };

    window.addEventListener('pointermove', updatePointerGlow);

    return () => {
      window.removeEventListener('pointermove', updatePointerGlow);
    };
  }, []);

  return (
    <div
      className="app"
      style={{
        '--pointer-x': `${pointerGlow.x}%`,
        '--pointer-y': `${pointerGlow.y}%`,
      }}
    >
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
