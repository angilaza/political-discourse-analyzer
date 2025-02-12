import React, { useState, useRef, useEffect } from 'react';
import { Send, History, Share2 } from 'lucide-react';
import logo from './assets/logo.png';
import ReactMarkdown from 'react-markdown';
import LegalNotice from './components/LegalNotice';
import LoadingIndicator from './components/LoadingIndicator';
import SuggestedQuestions from './components/SuggestedQuestions';
import ProgramsNotice from './components/ProgramsNotice';

const API_URL = import.meta.env.MODE === 'development' 
  ? 'http://localhost:8000' 
  : 'https://political-discourse-analyzer-production.up.railway.app';

interface Message {
  text: string;
  sender: 'user' | 'assistant';
  timestamp: Date;
  thread_id?: string;
}

// Header Component
const Header: React.FC<{
  mode: string;
  onNewConversation: () => void;
}> = ({ mode, onNewConversation }) => (
  <header className="flex items-center justify-between p-4 bg-white border-b">
    <div className="flex items-center gap-3">
      <img src={logo} alt="Logo" className="w-10 h-10" />
      <div>
        <h1 className="text-xl font-semibold">Comprende a tus Representantes</h1>
        <p className="text-sm text-gray-500">
          {mode === 'neutral' ? 'Consulta Programática' : 'Diálogo Personalizado'}
        </p>
      </div>
    </div>
    <div className="flex gap-2">
      <button 
        onClick={onNewConversation}
        className="px-4 py-2 text-sm text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
      >
        Nueva Conversación
      </button>
      <button className="p-2 hover:bg-gray-100 rounded-full transition-colors">
        <History className="w-5 h-5" />
      </button>
      <button className="p-2 hover:bg-gray-100 rounded-full transition-colors">
        <Share2 className="w-5 h-5" />
      </button>
    </div>
  </header>
);

// Message Component
const MessageComponent: React.FC<{ message: Message }> = ({ message }) => (
  <div className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
    <div
      className={`max-w-3xl p-4 rounded-lg ${
        message.sender === 'user'
          ? 'bg-blue-600 text-white'
          : 'bg-white border shadow-sm'
      }`}
    >
      <ReactMarkdown
        components={{
          h1: ({children}) => <h1 className="text-xl font-bold mb-4">{children}</h1>,
          h2: ({children}) => <h2 className="text-lg font-bold mb-3">{children}</h2>,
          ol: ({children}) => <ol className="list-decimal space-y-4 ml-4">{children}</ol>,
          ul: ({children}) => <ul className="list-disc space-y-2 ml-4">{children}</ul>,
          li: ({children}) => <li className="mb-2">{children}</li>,
          strong: ({children}) => <strong className="font-bold">{children}</strong>,
          p: ({children}) => <p className="mb-2">{children}</p>,
          blockquote: ({children}) => (
            <blockquote className="border-l-4 border-gray-300 pl-4 italic my-2">
              {children}
            </blockquote>
          )
        }}
        className="space-y-4"
      >
        {message.text}
      </ReactMarkdown>
    </div>
  </div>
);

// Messages Container Component
const MessagesContainer: React.FC<{
  messages: Message[];
  isLoading: boolean;
  onQuestionSelect: (question: string) => void;
}> = ({ messages, isLoading, onQuestionSelect }) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  if (messages.length === 0 && !isLoading) {
    return <SuggestedQuestions onQuestionClick={onQuestionSelect} />;
  }

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {messages.map((message, index) => (
        <MessageComponent key={index} message={message} />
      ))}
      {isLoading && <LoadingIndicator />}
      <div ref={messagesEndRef} />
    </div>
  );
};

// Mode Selector Component
const ModeSelector: React.FC<{
  mode: 'neutral' | 'personal';
  setMode: (mode: 'neutral' | 'personal') => void;
}> = ({ mode, setMode }) => (
  <div className="p-4 border-t bg-white">
    <div className="flex gap-2">
      <button
        onClick={() => setMode('neutral')}
        className={`px-4 py-2 rounded transition-colors ${
          mode === 'neutral'
            ? 'bg-blue-600 text-white'
            : 'bg-gray-100 hover:bg-gray-200 text-gray-800'
        }`}
      >
        Programas Electorales
      </button>
      <button
        onClick={() => setMode('personal')}
        disabled={mode === 'personal'}
        title="En desarrollo"
        className={`px-4 py-2 rounded transition-colors ${
          mode === 'neutral'
            ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
            : 'bg-gray-100 hover:bg-gray-200 text-gray-800'
        }`}
      >
        Perspectiva Personal
      </button>
    </div>
  </div>
);

// Main App Component
const App: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [mode, setMode] = useState<'neutral' | 'personal'>('neutral');
  const [isLoading, setIsLoading] = useState(false);
  const [currentThreadId, setCurrentThreadId] = useState<string | null>(null);

  const sendMessage = async (text: string) => {
    if (!text.trim() || isLoading) return;

    setMessages(prev => [...prev, {
      text,
      sender: 'user',
      timestamp: new Date()
    }]);
    setIsLoading(true);

    try {
      const response = await fetch(`${API_URL}/search`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
          query: text, 
          mode,
          thread_id: currentThreadId 
        })
      });

      const data = await response.json();
      
      if (!currentThreadId) {
        setCurrentThreadId(data.thread_id);
      }

      setMessages(prev => [...prev, {
        text: data.response || "Lo siento, hubo un error al procesar tu pregunta.",
        sender: 'assistant',
        timestamp: new Date(),
        thread_id: data.thread_id
      }]);
    } catch (error) {
      setMessages(prev => [...prev, {
        text: "Lo siento, ocurrió un error al comunicarse con el servidor.",
        sender: 'assistant',
        timestamp: new Date()
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await sendMessage(inputText);
    setInputText('');
  };

  const handleNewConversation = () => {
    setMessages([]);
    setCurrentThreadId(null);
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50 p-4">
      <LegalNotice />
      <Header mode={mode} onNewConversation={handleNewConversation} />
      
      <div className="bg-blue-50 border-b border-blue-100 px-4 py-2 text-xs text-blue-700">
        <p className="text-center">
          Proyecto de investigación universitaria · Versión Beta · 
          <span className="ml-1 font-medium">
            Las interacciones son almacenadas anónimamente con fines académicos
          </span>
        </p>
      </div>

      <ProgramsNotice />

      <div className="flex-1 overflow-y-auto mb-4">
        <MessagesContainer messages={messages} isLoading={isLoading} onQuestionSelect={(question) => setInputText(question)}/>
      </div>
      
      <ModeSelector mode={mode} setMode={setMode} />

      <form onSubmit={handleSubmit} className="border-t bg-white p-4">
        <div className="flex">
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Escribe tu pregunta sobre políticas y propuestas..."
            className="flex-1 p-3 border rounded-l-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading}
            className={`p-3 rounded-r-lg transition-colors focus:outline-none ${
              isLoading
                ? 'bg-gray-300 cursor-not-allowed'
                : 'bg-blue-600 text-white hover:bg-blue-700'
            }`}
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </form>
    </div>
  );
};

export default App;