import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { register, login } from '../../services/authService';
import './Register.css';

const Register = ({ onLogin }) => {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
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
      await register(formData.username, formData.email, formData.password);
      
      const loginData = await login(formData.username, formData.password);
      
      if (onLogin) {
        onLogin(loginData.user);
      }
      
      navigate('/starter-selection', { replace: true });
      
    } catch (err) {
      setError(err.message || 'Error al registrar usuario. Intenta con otro nombre de usuario o email.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="register-container">
      <div className="register-form">
        <h2>Registrarse</h2>
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
              placeholder="Ej: ashketchum"
            />
          </div>
          <div className="form-group">
            <label>Email:</label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              required
              disabled={loading}
              placeholder="Ej: ash@pokemon.com"
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
              placeholder="Mínimo 8 caracteres"
            />
          </div>
          {error && <div className="error-message">{error}</div>}
          <button type="submit" disabled={loading}>
            {loading ? 'Registrando...' : 'Comenzar Aventura'}
          </button>
        </form>
        <p>
          ¿Ya tienes cuenta? <Link to="/login">Inicia sesión aquí</Link>
        </p>
      </div>
    </div>
  );
};

export default Register;