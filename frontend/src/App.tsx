import React, { useState } from 'react';
import { Send, History, Share2 } from 'lucide-react';
import logo from './assets/logo.png';

interface Message {
  text: string;
  sender: 'user' | 'assistant';
  timestamp: Date;
}

interface MessageProps {
  message: Message;
}

const MessageComponent: React.FC<MessageProps> = ({ message }) => (
  <div className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
    <div
      style={{ whiteSpace: 'pre-wrap' }} // Esta línea asegura que los saltos de línea se respeten
      className={`max-w-3xl p-4 rounded-lg ${message.sender === 'user'
        ? 'bg-blue-600 text-white'
        : 'bg-white border shadow-sm'
        }`}
    >
      {message.text}
    </div>
  </div>
);

const App: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [mode, setMode] = useState<'neutral' | 'personal'>('neutral');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || isLoading) return;

    const newMessage: Message = {
      text: inputText,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, newMessage]);
    setInputText('');
    setIsLoading(true);

    try {
      const response = await fetch('https://political-discourse-analyzer-production.up.railway.app/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ query: inputText, mode })
      });

      const data = await response.json();

      setMessages(prev => [...prev, {
        text: data.response || "Lo siento, hubo un error al procesar tu pregunta.",
        sender: 'assistant',
        timestamp: new Date()
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

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
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