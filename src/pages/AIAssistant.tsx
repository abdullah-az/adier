import React, { useState } from 'react';
import { MessageCircle, Send, Brain, Loader } from 'lucide-react';

interface Message {
  id: number;
  text: string;
  sender: 'user' | 'ai';
  timestamp: Date;
}

const AIAssistant = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 1,
      text: "Hello! I'm your AI study assistant. How can I help you today?",
      sender: 'ai',
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSend = () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      id: messages.length + 1,
      text: input,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    // Simulate AI response
    setTimeout(() => {
      const aiMessage: Message = {
        id: messages.length + 2,
        text: "I understand you're asking about computer engineering concepts. Let me help explain that in detail...",
        sender: 'ai',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, aiMessage]);
      setIsLoading(false);
    }, 1000);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
        {/* Features Sidebar */}
        <div className="bg-white p-6 rounded-xl shadow-sm h-fit space-y-4">
          <h2 className="text-xl font-semibold text-gray-900 flex items-center">
            <Brain className="h-5 w-5 mr-2 text-indigo-600" />
            AI Features
          </h2>
          
          <button className="w-full text-left p-4 rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors">
            <h3 className="font-medium text-gray-900 mb-1">Question Generation</h3>
            <p className="text-sm text-gray-600">
              Generate practice questions based on specific topics
            </p>
          </button>
          
          <button className="w-full text-left p-4 rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors">
            <h3 className="font-medium text-gray-900 mb-1">Concept Explanation</h3>
            <p className="text-sm text-gray-600">
              Get detailed explanations of complex topics
            </p>
          </button>
          
          <button className="w-full text-left p-4 rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors">
            <h3 className="font-medium text-gray-900 mb-1">Problem Solving</h3>
            <p className="text-sm text-gray-600">
              Step-by-step guidance through problem-solving
            </p>
          </button>
        </div>

        {/* Chat Area */}
        <div className="md:col-span-3 bg-white rounded-xl shadow-sm flex flex-col h-[600px]">
          {/* Chat Header */}
          <div className="p-4 border-b">
            <div className="flex items-center space-x-2">
              <MessageCircle className="h-5 w-5 text-indigo-600" />
              <h2 className="text-lg font-semibold text-gray-900">AI Study Assistant</h2>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${
                  message.sender === 'user' ? 'justify-end' : 'justify-start'
                }`}
              >
                <div
                  className={`max-w-[80%] p-4 rounded-lg ${
                    message.sender === 'user'
                      ? 'bg-indigo-600 text-white'
                      : 'bg-gray-100 text-gray-900'
                  }`}
                >
                  {message.text}
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-gray-100 p-4 rounded-lg flex items-center space-x-2">
                  <Loader className="h-5 w-5 animate-spin text-indigo-600" />
                  <span className="text-gray-600">Thinking...</span>
                </div>
              </div>
            )}
          </div>

          {/* Input Area */}
          <div className="p-4 border-t">
            <div className="flex space-x-4">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                placeholder="Ask anything about computer engineering..."
                className="flex-1 p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-600"
              />
              <button
                onClick={handleSend}
                disabled={!input.trim()}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Send className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AIAssistant;