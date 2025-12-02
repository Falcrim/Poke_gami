import React, { useState, useRef, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import './Navbar.css';

const Navbar = ({ user, onLogout }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const [showMultiplayerMenu, setShowMultiplayerMenu] = useState(false);
  const menuRef = useRef(null);

  const handleLogout = () => {
    onLogout();
    navigate('/login');
  };

  const toggleMultiplayerMenu = () => {
    setShowMultiplayerMenu(!showMultiplayerMenu);
  };

  const handleCreateRoom = () => {
    setShowMultiplayerMenu(false);
    navigate('/create-room');
  };

  const handleViewRooms = () => {
    setShowMultiplayerMenu(false);
    navigate('/view-rooms');
  };

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setShowMultiplayerMenu(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

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

        <div className="multiplayer-container" ref={menuRef}>
          <button
            className={`multiplayer-btn ${showMultiplayerMenu ? 'active' : ''}`}
            onClick={toggleMultiplayerMenu}
          >
            Multijugador
            <span className="dropdown-arrow">▼</span>
          </button>

          {showMultiplayerMenu && (
            <div className="multiplayer-dropdown">
              <button
                className="dropdown-item"
                onClick={handleCreateRoom}
              >
                <span className="dropdown-icon">➕</span>
                Crear Sala
              </button>
              <button
                className="dropdown-item"
                onClick={handleViewRooms}
              >
                <span className="dropdown-icon">👁️</span>
                Ver Salas
              </button>
            </div>
          )}
        </div>

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