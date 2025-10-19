import React, { useState, useEffect } from 'react';
import type { Message } from './types';
import { MOCK_MESSAGES } from './constants';

const API_BASE_URL = 'http://localhost:3001/api';

const App: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);

  // Fetch data from API
  const fetchData = async () => {
    try {
      const messagesRes = await fetch(`${API_BASE_URL}/messages`);
      const messagesData = await messagesRes.json();

      // If no real data, use mock data
      if (messagesData.length === 0) {
        setMessages(MOCK_MESSAGES);
      } else {
        setMessages(messagesData);
      }
    } catch (error) {
      console.error('Error fetching data:', error);
      // Fallback to mock data
      setMessages(MOCK_MESSAGES);
    } finally {
      setLoading(false);
    }
  };

  // Initial fetch
  useEffect(() => {
    fetchData();
  }, []);

  // Poll for updates every 3 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      fetchData();
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 text-gray-100 flex items-center justify-center">
        <div className="text-xl">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100">
      <div className="max-w-3xl mx-auto p-6">
        <h1 className="text-2xl font-bold mb-6">Messages</h1>

        <div className="space-y-4">
          {messages.map((message) => (
            <div key={message.id} className="bg-gray-800 rounded-lg p-4 border border-gray-700">
              <div className="text-sm text-gray-400 mb-2">
                {message.from}
              </div>
              <div className="text-gray-100">
                {message.text}
              </div>
              <div className="text-xs text-gray-500 mt-2">
                {new Date(message.timestamp).toLocaleString()}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default App;
