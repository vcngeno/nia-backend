import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { conversationAPI } from '../../services/api';

export default function Chat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const messagesEndRef = useRef(null);
  const navigate = useNavigate();

  const child = JSON.parse(localStorage.getItem('currentChild') || '{}');

  const exitChildSession = () => {
    localStorage.removeItem('childToken');
    localStorage.removeItem('currentChild');
    navigate('/dashboard');
  };

  useEffect(() => {
    if (!child.id) {
      navigate('/dashboard');
    }
  }, [child.id, navigate]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setLoading(true);

    try {
      const response = await conversationAPI.sendMessage({
        child_id: child.id,
        message: userMessage,
        conversation_id: conversationId,
        depth_level: 1,
      });

      setConversationId(response.data.conversation_id);
      setMessages(prev => [...prev, { role: 'assistant', content: response.data.message.content }]);
    } catch (error) {
      console.error('Failed to send message:', error);
      setMessages(prev => [...prev, { role: 'assistant', content: "Oops! I had trouble with that. Can you try asking again?" }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
      <div style={{ background: 'white', padding: '20px', boxShadow: '0 2px 10px rgba(0,0,0,0.1)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
          <div style={{ width: '50px', height: '50px', borderRadius: '50%', background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontSize: '1.5rem', fontWeight: 'bold' }}>
            N
          </div>
          <div>
            <h2 style={{ margin: 0, fontSize: '1.5rem' }}>Nia - Your Learning Friend! 🎓</h2>
            <p style={{ margin: 0, color: '#666', fontSize: '0.9rem' }}>Hi {child.name}! Ask me anything!</p>
          </div>
        </div>
        <button onClick={exitChildSession} style={{ background: '#f44336', color: 'white', padding: '10px 20px', border: 'none', borderRadius: '8px', cursor: 'pointer', fontWeight: '600' }}>
          Exit
        </button>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: '30px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
        {messages.length === 0 && (
          <div style={{ textAlign: 'center', color: 'white', marginTop: '50px' }}>
            <h2 style={{ fontSize: '2.5rem', marginBottom: '20px' }}>👋 Hello {child.name}!</h2>
            <p style={{ fontSize: '1.3rem', marginBottom: '30px' }}>I'm Nia, and I'm here to help you learn!</p>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '15px', justifyContent: 'center', maxWidth: '800px', margin: '0 auto' }}>
              {['What is 5 + 3?', 'Tell me about planets', 'How do plants grow?', 'What is a noun?'].map((q) => (
                <button key={q} onClick={() => { setInput(q); setTimeout(() => handleSend({ preventDefault: () => {} }), 100); }} style={{ background: 'white', padding: '15px 25px', borderRadius: '15px', border: 'none', cursor: 'pointer', fontSize: '1rem', fontWeight: '600', color: '#667eea', boxShadow: '0 5px 15px rgba(0,0,0,0.2)' }}>
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div key={idx} style={{ display: 'flex', justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
            <div style={{ maxWidth: '70%', padding: '15px 20px', borderRadius: '20px', background: msg.role === 'user' ? '#667eea' : 'white', color: msg.role === 'user' ? 'white' : '#333', boxShadow: '0 5px 15px rgba(0,0,0,0.2)', fontSize: '1.1rem', lineHeight: '1.6' }}>
              {msg.content}
            </div>
          </div>
        ))}

        {loading && (
          <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
            <div style={{ background: 'white', padding: '15px 20px', borderRadius: '20px', boxShadow: '0 5px 15px rgba(0,0,0,0.2)' }}>
              <div style={{ display: 'flex', gap: '5px' }}>
                <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#667eea', animation: 'bounce 1s infinite' }}></div>
                <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#667eea', animation: 'bounce 1s infinite 0.2s' }}></div>
                <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#667eea', animation: 'bounce 1s infinite 0.4s' }}></div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSend} style={{ padding: '20px', background: 'white', boxShadow: '0 -2px 10px rgba(0,0,0,0.1)' }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto', display: 'flex', gap: '10px' }}>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value.slice(0, 4000))}
            maxLength={4000}
            placeholder="Ask me anything..."
            style={{ flex: 1, padding: '15px 20px', border: '2px solid #e0e0e0', borderRadius: '15px', fontSize: '1.1rem', outline: 'none' }}
            disabled={loading}
          />
          <button type="submit" disabled={loading || !input.trim()} style={{ padding: '15px 40px', background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white', border: 'none', borderRadius: '15px', fontSize: '1.1rem', fontWeight: '600', cursor: 'pointer', opacity: !input.trim() ? 0.5 : 1 }}>
            Send 🚀
          </button>
        </div>
      </form>
    </div>
  );
}
