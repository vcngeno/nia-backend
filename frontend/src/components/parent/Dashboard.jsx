import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { childrenAPI } from '../../services/api';

export default function Dashboard() {
  const [children, setChildren] = useState([]);
  const [showAddChild, setShowAddChild] = useState(false);
  const [loading, setLoading] = useState(true);
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    loadChildren();
  }, []);

  const loadChildren = async () => {
    try {
      const response = await childrenAPI.getAll();
      setChildren(response.data);
    } catch (err) {
      console.error('Failed to load children:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <div>
          <h1 style={styles.title}>Parent Dashboard</h1>
          <p style={styles.subtitle}>Welcome, {user?.full_name}!</p>
        </div>
        <button onClick={logout} style={styles.logoutBtn}>
          Logout
        </button>
      </div>

      <div style={styles.content}>
        <div style={styles.section}>
          <div style={styles.sectionHeader}>
            <h2>Your Children</h2>
            <button onClick={() => setShowAddChild(true)} style={styles.addBtn}>
              + Add Child
            </button>
          </div>

          {loading ? (
            <p>Loading...</p>
          ) : children.length === 0 ? (
            <div style={styles.emptyState}>
              <p style={styles.emptyText}>No children added yet</p>
              <button onClick={() => setShowAddChild(true)} style={styles.primaryBtn}>
                Add Your First Child
              </button>
            </div>
          ) : (
            <div style={styles.childrenGrid}>
              {children.map((child) => (
                <div key={child.id} style={styles.childCard}>
                  <div style={styles.childIcon}>
                    {child.name.charAt(0).toUpperCase()}
                  </div>
                  <h3 style={styles.childName}>{child.name}</h3>
                  <p style={styles.childInfo}>
                    {child.age} years old • Grade {child.grade_level}
                  </p>
                  <button
                    onClick={() => {
                      localStorage.setItem('currentChild', JSON.stringify(child));
                      navigate('/child-login');
                    }}
                    style={styles.selectBtn}
                  >
                    Select Child
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {showAddChild && (
        <AddChildModal
          onClose={() => setShowAddChild(false)}
          onSuccess={() => {
            setShowAddChild(false);
            loadChildren();
          }}
        />
      )}
    </div>
  );
}

function AddChildModal({ onClose, onSuccess }) {
  const [formData, setFormData] = useState({
    name: '',
    age: '',
    grade_level: '1st',
    pin: '',
    language: 'english',
    // Accessibility options
    has_autism: false,
    has_dyslexia: false,
    has_adhd: false,
    is_visual_learner: false,
    use_simplified_language: false,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const gradeOptions = [
    'kindergarten', '1st', '2nd', '3rd', '4th', '5th',
    '6th', '7th', '8th', '9th', '10th', '11th', '12th'
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await childrenAPI.create({
        ...formData,
        age: parseInt(formData.age),
      });
      onSuccess();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create child profile');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.modalOverlay} onClick={onClose}>
      <div style={styles.modalLarge} onClick={(e) => e.stopPropagation()}>
        <h2 style={styles.modalTitle}>Add Child Profile</h2>

        <form onSubmit={handleSubmit} style={styles.form}>
          {error && <div style={styles.error}>{error}</div>}

          <div style={styles.formGroup}>
            <label style={styles.label}>Child's Name</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
              style={styles.input}
            />
          </div>

          <div style={styles.formGroup}>
            <label style={styles.label}>Age</label>
            <input
              type="number"
              value={formData.age}
              onChange={(e) => setFormData({ ...formData, age: e.target.value })}
              required
              min="5"
              max="18"
              style={styles.input}
            />
          </div>

          <div style={styles.formGroup}>
            <label style={styles.label}>Grade Level</label>
            <select
              value={formData.grade_level}
              onChange={(e) => setFormData({ ...formData, grade_level: e.target.value })}
              style={styles.input}
            >
              {gradeOptions.map((grade) => (
                <option key={grade} value={grade}>
                  {grade}
                </option>
              ))}
            </select>
          </div>

          <div style={styles.formGroup}>
            <label style={styles.label}>PIN (4 digits)</label>
            <input
              type="text"
              value={formData.pin}
              onChange={(e) => setFormData({ ...formData, pin: e.target.value })}
              required
              maxLength="4"
              pattern="[0-9]{4}"
              placeholder="1234"
              style={styles.input}
            />
          </div>

          {/* Learning Accommodations Section */}
          <div style={styles.formGroup}>
            <label style={styles.sectionLabel}>
              🌟 Learning Accommodations (Optional)
            </label>
            <p style={styles.helpText}>
              Select any that apply to customize Nia's teaching style for your child
            </p>

            <div style={styles.checkboxGroup}>
              <label style={styles.checkboxLabel}>
                <input
                  type="checkbox"
                  checked={formData.has_autism}
                  onChange={(e) => setFormData({ ...formData, has_autism: e.target.checked })}
                  style={styles.checkbox}
                />
                <span style={styles.checkboxText}>
                  <strong>Autism Spectrum Disorder</strong>
                  <br />
                  <small>Uses literal language, structured responses, avoids idioms</small>
                </span>
              </label>

              <label style={styles.checkboxLabel}>
                <input
                  type="checkbox"
                  checked={formData.has_dyslexia}
                  onChange={(e) => setFormData({ ...formData, has_dyslexia: e.target.checked })}
                  style={styles.checkbox}
                />
                <span style={styles.checkboxText}>
                  <strong>Dyslexia</strong>
                  <br />
                  <small>Simple sentences, clear formatting, common words</small>
                </span>
              </label>

              <label style={styles.checkboxLabel}>
                <input
                  type="checkbox"
                  checked={formData.has_adhd}
                  onChange={(e) => setFormData({ ...formData, has_adhd: e.target.checked })}
                  style={styles.checkbox}
                />
                <span style={styles.checkboxText}>
                  <strong>ADHD</strong>
                  <br />
                  <small>Concise responses, bullet points, frequent engagement</small>
                </span>
              </label>

              <label style={styles.checkboxLabel}>
                <input
                  type="checkbox"
                  checked={formData.is_visual_learner}
                  onChange={(e) => setFormData({ ...formData, is_visual_learner: e.target.checked })}
                  style={styles.checkbox}
                />
                <span style={styles.checkboxText}>
                  <strong>Visual Learner</strong>
                  <br />
                  <small>Spatial descriptions, suggests visual representations</small>
                </span>
              </label>

              <label style={styles.checkboxLabel}>
                <input
                  type="checkbox"
                  checked={formData.use_simplified_language}
                  onChange={(e) => setFormData({ ...formData, use_simplified_language: e.target.checked })}
                  style={styles.checkbox}
                />
                <span style={styles.checkboxText}>
                  <strong>Simplified Language</strong>
                  <br />
                  <small>Very simple words, short sentences, basic vocabulary</small>
                </span>
              </label>
            </div>
          </div>

          <div style={styles.modalButtons}>
            <button type="button" onClick={onClose} style={styles.cancelBtn}>
              Cancel
            </button>
            <button type="submit" disabled={loading} style={styles.submitBtn}>
              {loading ? 'Creating...' : 'Add Child'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

const styles = {
  container: {
    minHeight: '100vh',
    background: '#f5f7fa',
  },
  header: {
    background: 'white',
    padding: '30px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  title: {
    fontSize: '2rem',
    margin: 0,
    color: '#333',
  },
  subtitle: {
    color: '#666',
    margin: '5px 0 0 0',
  },
  logoutBtn: {
    background: '#f44336',
    color: 'white',
    padding: '10px 20px',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
    fontWeight: '600',
  },
  content: {
    maxWidth: '1200px',
    margin: '40px auto',
    padding: '0 20px',
  },
  section: {
    background: 'white',
    borderRadius: '15px',
    padding: '30px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
  },
  sectionHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '30px',
  },
  addBtn: {
    background: '#667eea',
    color: 'white',
    padding: '12px 24px',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
    fontWeight: '600',
  },
  emptyState: {
    textAlign: 'center',
    padding: '60px 20px',
  },
  emptyText: {
    color: '#999',
    fontSize: '1.1rem',
    marginBottom: '20px',
  },
  primaryBtn: {
    background: '#667eea',
    color: 'white',
    padding: '15px 30px',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
    fontSize: '1rem',
    fontWeight: '600',
  },
  childrenGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))',
    gap: '20px',
  },
  childCard: {
    background: '#f8f9fa',
    padding: '25px',
    borderRadius: '12px',
    textAlign: 'center',
  },
  childIcon: {
    width: '80px',
    height: '80px',
    borderRadius: '50%',
    background: '#667eea',
    color: 'white',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '2rem',
    fontWeight: 'bold',
    margin: '0 auto 15px',
  },
  childName: {
    fontSize: '1.3rem',
    margin: '0 0 10px 0',
    color: '#333',
  },
  childInfo: {
    color: '#666',
    margin: '0 0 20px 0',
  },
  selectBtn: {
    background: '#667eea',
    color: 'white',
    padding: '10px 20px',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
    width: '100%',
    fontWeight: '600',
  },
  modalOverlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    background: 'rgba(0,0,0,0.5)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1000,
  },
  modalLarge: {
    background: 'white',
    borderRadius: '15px',
    padding: '30px',
    maxWidth: '600px',
    width: '90%',
    maxHeight: '90vh',
    overflowY: 'auto',
  },
  modalTitle: {
    margin: '0 0 25px 0',
    fontSize: '1.8rem',
    color: '#333',
  },
  form: {
    display: 'flex',
    flexDirection: 'column',
    gap: '20px',
  },
  formGroup: {
    display: 'flex',
    flexDirection: 'column',
  },
  label: {
    marginBottom: '8px',
    fontWeight: '600',
    color: '#333',
  },
  sectionLabel: {
    display: 'block',
    fontSize: '1.1rem',
    fontWeight: '600',
    color: '#333',
    marginBottom: '8px',
  },
  helpText: {
    color: '#666',
    fontSize: '0.9rem',
    margin: '0 0 15px 0',
  },
  input: {
    padding: '12px',
    border: '2px solid #e0e0e0',
    borderRadius: '8px',
    fontSize: '1rem',
  },
  checkboxGroup: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  checkboxLabel: {
    display: 'flex',
    alignItems: 'start',
    padding: '12px',
    background: '#f8f9fa',
    borderRadius: '8px',
    cursor: 'pointer',
    transition: 'background 0.2s',
    border: '2px solid transparent',
  },
  checkbox: {
    width: '20px',
    height: '20px',
    marginRight: '12px',
    marginTop: '2px',
    cursor: 'pointer',
    accentColor: '#667eea',
  },
  checkboxText: {
    flex: 1,
    color: '#333',
    fontSize: '0.95rem',
  },
  error: {
    background: '#fee',
    color: '#c33',
    padding: '12px',
    borderRadius: '8px',
    marginBottom: '15px',
  },
  modalButtons: {
    display: 'flex',
    gap: '15px',
    marginTop: '10px',
  },
  cancelBtn: {
    flex: 1,
    padding: '12px',
    background: '#e0e0e0',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
    fontWeight: '600',
  },
  submitBtn: {
    flex: 1,
    padding: '12px',
    background: '#667eea',
    color: 'white',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
    fontWeight: '600',
  },
};
