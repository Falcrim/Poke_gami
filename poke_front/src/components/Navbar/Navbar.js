import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import './Navbar.css';

const Navbar = ({ user, onLogout }) => {
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = () => {
    onLogout();
    navigate('/login');
  };

  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <h2>Pokémon Fire Red</h2>
      </div>
      <div className="navbar-menu">
        <Link 
          to="/dashboard" 
          className={`nav-link ${location.pathname === '/dashboard' ? 'active' : ''}`}
        >
          Dashboard
        </Link>
        <Link 
          to="/pokedex" 
          className={`nav-link ${location.pathname === '/pokedex' ? 'active' : ''}`}
        >
          Pokédex
        </Link>
        <Link 
          to="/profile" 
          className={`nav-link ${location.pathname === '/profile' ? 'active' : ''}`}
        >
          {user?.username || 'Perfil'}
        </Link>
        <Link 
          to="/ranking" 
          className={`nav-link ${location.pathname === '/ranking' ? 'active' : ''}`}
        >
          Ranking
        </Link>
        <button onClick={handleLogout} className="logout-btn">
          Cerrar Sesión
        </button>
      </div>
    </nav>
  );
};

export default Navbar;