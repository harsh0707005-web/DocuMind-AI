import { useState, useEffect, useRef } from 'react';
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

  return (
    <div className="app">
      <Sidebar
        conversations={conversations}
        setConversations={setConversations}
        activeConversation={activeConversation}
        setActiveConversation={setActiveConversation}
        setMessages={setMessages}
        sidebarOpen={sidebarOpen}
        setSidebarOpen={setSidebarOpen}
      />
      <main className={`main-content ${sidebarOpen ? '' : 'sidebar-closed'}`}>
        <Header
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          model={model}
          setModel={setModel}
          sidebarOpen={sidebarOpen}
          setSidebarOpen={setSidebarOpen}
        />
        <div className="content-area">
          {activeTab === 'chat' && (
            <ChatWindow
              messages={messages}
              setMessages={setMessages}
              activeConversation={activeConversation}
              setActiveConversation={setActiveConversation}
              conversations={conversations}
              setConversations={setConversations}
              model={model}
            />
          )}
          {activeTab === 'documents' && (
            <DocumentUpload
              documents={documents}
              setDocuments={setDocuments}
            />
          )}
          {activeTab === 'study' && (
            <StudyTools model={model} />
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
