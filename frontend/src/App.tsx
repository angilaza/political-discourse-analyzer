import React, { useState } from 'react';
import { Send, History, Share2 } from 'lucide-react';
import logo from './assets/logo.png';
import ReactMarkdown from 'react-markdown';

const API_URL = import.meta.env.MODE === 'development' ? 'http://localhost:8000' : 'https://political-discourse-analyzer-production.up.railway.app';
interface Message {
 text: string;
 sender: 'user' | 'assistant';
 timestamp: Date;
 thread_id?: string;
}

interface MessageProps {
 message: Message;
}

const MessageComponent: React.FC<MessageProps> = ({ message }) => (
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
          // Configurar cómo se renderizan los elementos Markdown
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

const App: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [mode, setMode] = useState<'neutral' | 'personal'>('neutral');
  const [isLoading, setIsLoading] = useState(false);
  const [currentThreadId, setCurrentThreadId] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || isLoading) return;
  
    setMessages(prev => [...prev, {
      text: inputText,
      sender: 'user',
      timestamp: new Date()
    }]);
    setInputText('');
    setIsLoading(true);
  
    const tempMessage = {
      text: '',
      sender: 'assistant' as const,
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, tempMessage]);
  
    try {
      const response = await fetch(`${API_URL}/search/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          query: inputText, 
          mode,
          thread_id: currentThreadId 
        })
      });
  
      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No reader available');
      }
  
      let lastText = '';
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
  
        const chunk = new TextDecoder().decode(value);
        const lines = chunk.split('\n');
  
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = JSON.parse(line.slice(6));
            
            if (data.type === 'token') {
              setMessages(prev => {
                const newMessages = [...prev];
                const lastMessage = newMessages[newMessages.length - 1];
                const newContent = data.content.trim();
                
                // Evitar duplicados verificando que el nuevo contenido no esté ya al final
                if (!lastMessage.text.endsWith(newContent)) {
                  lastMessage.text = (lastMessage.text + ' ' + newContent).trim();
                }
                
                return newMessages;
              });
            } else if (data.type === 'done') {
              if (!currentThreadId) {
                setCurrentThreadId(data.thread_id);
              }
              setIsLoading(false);
              break;
            }
          }
        }
      }
    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, {
        text: "Error al comunicarse con el servidor.",
        sender: 'assistant',
        timestamp: new Date()
      }]);
      setIsLoading(false);
    }
  };

  // Añadir función para limpiar la conversación
  const handleNewConversation = () => {
    setMessages([]);
    setCurrentThreadId(null);
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header con botón de nueva conversación */}
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
            onClick={handleNewConversation}
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

      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message, index) => (
          <MessageComponent key={index} message={message} />
        ))}
      </div>

      {/* Mode Selector */}
      <div className="p-4 border-t bg-white">
        <div className="flex gap-2">
          <button
            onClick={() => setMode('neutral')}
            className={`px-4 py-2 rounded transition-colors ${mode === 'neutral'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 hover:bg-gray-200'
              }`}
          >
            Programas Electorales
          </button>
          <button
            onClick={() => setMode('personal')}
            className={`px-4 py-2 rounded transition-colors ${mode === 'personal'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 hover:bg-gray-200'
              }`}
          >
            Perspectiva Personal
          </button>
        </div>
      </div>

      {/* Input Area */}
      <form onSubmit={handleSubmit} className="p-4 border-t bg-white">
        <div className="flex gap-2">
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Escribe tu pregunta sobre políticas y propuestas..."
            className="flex-1 p-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading}
            className={`p-3 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 ${isLoading
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