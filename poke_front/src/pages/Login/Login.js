import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { login } from '../../services/authService';
import './Login.css';

const Login = ({ onLogin }) => {
  const [formData, setFormData] = useState({
    username: '',
    password: ''
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const data = await login(formData.username, formData.password);
      onLogin(data.user);
      
      if (!data.user.player_info.starter_chosen) {
        navigate('/starter-selection');
      } else {
        navigate('/dashboard');
      }
    } catch (err) {
      setError(err.message || 'Error al iniciar sesión. Verifica tus credenciales.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-form">
        <h2>Iniciar Sesión</h2>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Usuario:</label>
            <input
              type="text"
              name="username"
              value={formData.username}
              onChange={handleChange}
              required
              disabled={loading}
            />
          </div>
          <div className="form-group">
            <label>Contraseña:</label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              required
              disabled={loading}
            />
          </div>
          {error && <div className="error-message">{error}</div>}
          <button type="submit" disabled={loading}>
            {loading ? 'Iniciando Sesión...' : 'Iniciar Sesión'}
          </button>
        </form>
        <p>
          ¿No tienes cuenta? <Link to="/register">Regístrate aquí</Link>
        </p>
      </div>
    </div>
  );
};

export default Login;