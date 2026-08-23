import React, { useState, useRef, useEffect } from 'react';
import { 
  Send, 
  Stethoscope, 
  Clock, 
  FileText, 
  Settings, 
  Plus, 
  CheckCircle2,
  AlertCircle,
  Trash2
} from 'lucide-react';

type Message = {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  confidence?: number;
  citations?: { id: number; source: string; snippet: string; url?: string }[];
};

type SavedProtocol = {
  id: string;
  title: string;
  messages: Message[];
};

export default function App() {
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  
  const initialMessage: Message = {
    id: '1',
    role: 'assistant',
    content: 'Welcome to the Healthcare Knowledge Navigator. I am connected to the real RAG backend. Ask me about the ADA diabetes guidelines, hypertension, or any other clinical topic!'
  };

  const [messages, setMessages] = useState<Message[]>([initialMessage]);
  const [savedProtocols, setSavedProtocols] = useState<SavedProtocol[]>([]);
  
  const chatContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTo({
        top: chatContainerRef.current.scrollHeight,
        behavior: 'smooth'
      });
    }
  }, [messages, isTyping]);

  const handleNewConsultation = () => {
    if (messages.length > 1) {
      // Find the first user message to use as the title
      const firstUserMsg = messages.find(m => m.role === 'user');
      const title = firstUserMsg 
        ? firstUserMsg.content.substring(0, 30) + (firstUserMsg.content.length > 30 ? '...' : '') 
        : 'Consultation';
        
      setSavedProtocols(prev => [{
        id: Date.now().toString(),
        title,
        messages: [...messages]
      }, ...prev]);
    }
    
    // Reset the chat
    setMessages([{
      id: Date.now().toString(),
      role: 'assistant',
      content: 'Welcome to a new consultation. How can I assist you today?'
    }]);
  };

  const handleDeleteProtocol = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setSavedProtocols(prev => prev.filter(p => p.id !== id));
  };

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsTyping(true);

    try {
      const response = await fetch('http://localhost:8000/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: userMessage.content })
      });
      
      const data = await response.json();
      
      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.answer,
        confidence: data.confidence,
        citations: data.citations
      };
      
      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error(error);
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Error connecting to the RAG backend. Is FastAPI running on port 8000?'
      }]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="app-container">
      {/* Background Decorators */}
      <div className="bg-blob blob-1"></div>
      <div className="bg-blob blob-2"></div>

      {/* Sidebar */}
      <aside className="sidebar glass">
        <div className="brand">
          <Stethoscope size={28} color="#dc2626" />
          <h1>MedNavigator</h1>
        </div>

        <button className="new-chat-btn" onClick={handleNewConsultation}>
          <Plus size={18} />
          New Consultation
        </button>

        <div className="nav-item active">
          <Clock size={18} />
          <span>Recent Queries</span>
        </div>
        
        <div className="nav-item" style={{ marginTop: '1rem', pointerEvents: 'none' }}>
          <FileText size={18} />
          <span style={{ fontWeight: 600 }}>Saved Protocols</span>
        </div>
        
        <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '0.25rem', paddingLeft: '1rem' }}>
          {savedProtocols.length === 0 ? (
            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>No saved protocols yet.</div>
          ) : (
            savedProtocols.map(protocol => (
              <div 
                key={protocol.id} 
                className="nav-item" 
                style={{ fontSize: '0.875rem', padding: '0.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }} 
                onClick={() => setMessages(protocol.messages)}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', overflow: 'hidden' }}>
                  <FileText size={14} style={{ flexShrink: 0 }} />
                  <span style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {protocol.title}
                  </span>
                </div>
                <button 
                  onClick={(e) => handleDeleteProtocol(protocol.id, e)}
                  className="delete-btn"
                  title="Delete saved protocol"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            ))
          )}
        </div>
        
        <div className="nav-item">
          <Settings size={18} />
          <span>Settings</span>
        </div>
      </aside>

      {/* Main Chat Area */}
      <main className="main-content">
        <div className="chat-container" ref={chatContainerRef}>
          {messages.map((msg) => (
            <div key={msg.id} className={`message ${msg.role}`}>
              {msg.role === 'assistant' && (
                <div className="glass" style={{ width: '100%', padding: '1.5rem', borderRadius: '0 20px 20px 20px' }}>
                  {msg.confidence !== undefined && msg.confidence > 0 && msg.citations && msg.citations.length > 0 && (
                    <div className="confidence-badge" style={{ 
                      color: msg.confidence >= 80 ? 'var(--success-color)' : '#dc2626',
                      background: msg.confidence >= 80 ? 'rgba(16, 185, 129, 0.1)' : 'rgba(220, 38, 38, 0.1)',
                      borderColor: msg.confidence >= 80 ? 'rgba(16, 185, 129, 0.2)' : 'rgba(220, 38, 38, 0.2)'
                    }}>
                      {msg.confidence >= 80 ? <CheckCircle2 size={16} /> : <AlertCircle size={16} />}
                      Confidence: {msg.confidence}%
                    </div>
                  )}
                  
                  <div className="markdown-content">
                    {msg.content.split('\n').map((line, i) => (
                      <p key={i}>
                        {line.split('**').map((part, j) => j % 2 === 1 ? <strong key={j}>{part}</strong> : part)}
                      </p>
                    ))}
                  </div>

                  {msg.citations && msg.citations.length > 0 && (
                    <div className="citations-box">
                      <h4 className="mb-2" style={{ color: 'var(--text-muted)' }}>Retrieved Context Sources:</h4>
                      {msg.citations.map((cit) => (
                        <div key={cit.id} className="citation-item">
                          <span className="citation-ref">[{cit.id}]</span>
                          <span><strong>{cit.source}</strong>: "{cit.snippet}"</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
              {msg.role === 'user' && (
                <div>{msg.content}</div>
              )}
            </div>
          ))}
          
          {isTyping && (
            <div className="message bot">
              <div className="glass" style={{ width: 'fit-content', padding: '1rem', borderRadius: '0 20px 20px 20px' }}>
                <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                  <div className="typing-dot" style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--primary-color)', animation: 'pulse 1s infinite' }} />
                  <div className="typing-dot" style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--primary-color)', animation: 'pulse 1s infinite 0.2s' }} />
                  <div className="typing-dot" style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--primary-color)', animation: 'pulse 1s infinite 0.4s' }} />
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="input-area glass">
          <div className="input-wrapper">
            <input
              type="text"
              className="chat-input"
              placeholder="Ask about clinical guidelines, treatments, or research papers..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
            />
            <button 
              className="send-button" 
              onClick={handleSend}
              disabled={!input.trim() || isTyping}
            >
              <Send size={18} />
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
