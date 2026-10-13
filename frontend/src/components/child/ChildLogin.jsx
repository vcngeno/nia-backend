import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { childrenAPI } from '../../services/api';

export default function ChildLogin() {
  const [pin, setPin] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const child = JSON.parse(localStorage.getItem('currentChild') || '{}');

  if (!child.id) {
    navigate('/dashboard');
    return null;
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    localStorage.removeItem('childToken');

    try {
      const response = await childrenAPI.login({ child_id: child.id, pin });
      localStorage.setItem('childToken', response.data.access_token);
      navigate('/chat');
    } catch {
      setError('Incorrect PIN. Try again!');
      setPin('');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)' }}>
      <div style={{ background: 'white', borderRadius: '30px', padding: '50px', textAlign: 'center', maxWidth: '400px', boxShadow: '0 20px 60px rgba(0,0,0,0.3)' }}>
        <div style={{ width: '100px', height: '100px', borderRadius: '50%', background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 20px', fontSize: '3rem', color: 'white' }}>
          {child.name?.[0]?.toUpperCase()}
        </div>

        <h1 style={{ fontSize: '2rem', marginBottom: '10px' }}>Hi {child.name}! 👋</h1>
        <p style={{ color: '#666', marginBottom: '30px' }}>Enter your PIN to start learning</p>

        <form onSubmit={handleSubmit}>
          {error && <div style={{ background: '#fee', color: '#c33', padding: '12px', borderRadius: '10px', marginBottom: '20px' }}>{error}</div>}

          <input
            type="password"
            inputMode="numeric"
            pattern="[0-9]*"
            maxLength="4"
            value={pin}
            onChange={(e) => setPin(e.target.value.replace(/\D/g, ''))}
            placeholder="••••"
            style={{ width: '100%', padding: '20px', fontSize: '2rem', textAlign: 'center', border: '3px solid #e0e0e0', borderRadius: '15px', marginBottom: '20px', letterSpacing: '10px' }}
            autoFocus
          />

          <button type="submit" disabled={loading || pin.length !== 4} style={{ width: '100%', padding: '18px', background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white', border: 'none', borderRadius: '15px', fontSize: '1.2rem', fontWeight: '600', cursor: 'pointer', opacity: pin.length !== 4 ? 0.5 : 1 }}>
            {loading ? 'Checking...' : 'Start Learning! 🚀'}
          </button>
        </form>

        <button onClick={() => navigate('/dashboard')} style={{ marginTop: '20px', background: 'none', border: 'none', color: '#667eea', cursor: 'pointer', textDecoration: 'underline' }}>
          Back to Dashboard
        </button>
      </div>
    </div>
  );
}
