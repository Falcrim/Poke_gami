import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getStarters } from '../../services/gameService';
import { chooseStarter } from '../../services/authService';
import './StarterSelection.css';

const StarterSelection = ({ onStarterSelected }) => {
  const [starters, setStarters] = useState([]);
  const [selectedStarter, setSelectedStarter] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const fetchStarters = async () => {
      try {
        const data = await getStarters();
        setStarters(data);
      } catch (err) {
        setError('Error al cargar los Pokémon iniciales');
      } finally {
        setLoading(false);
      }
    };

    fetchStarters();
  }, []);

  const handleSelectStarter = async () => {
    if (!selectedStarter) {
      setError('Por favor selecciona un Pokémon');
      return;
    }

    setSubmitting(true);
    setError('');
    
    try {
      // Hacer POST para seleccionar el starter
      await chooseStarter(selectedStarter.id);
      
      // Notificar al App.js que se seleccionó el starter
      if (onStarterSelected) {
        onStarterSelected();
      }
      
      // Redirigir al dashboard después de seleccionar
      navigate('/dashboard', { replace: true });
      
    } catch (err) {
      setError(err.message || 'Error al seleccionar el Pokémon');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="loading-spinner"></div>
        <p>Cargando Pokémon iniciales...</p>
      </div>
    );
  }

  return (
    <div className="starter-selection">
      <div className="selection-container">
        <h2>¡Elige tu Pokémon Inicial!</h2>
        <p>Selecciona a tu compañero de aventuras</p>
        
        {error && <div className="error-message">{error}</div>}
        
        <div className="starters-grid">
          {starters.map((starter) => (
            <div
              key={starter.id}
              className={`starter-card ${selectedStarter?.id === starter.id ? 'selected' : ''}`}
              onClick={() => {
                setSelectedStarter(starter);
                setError('');
              }}
            >
              <img src={starter.sprite_front} alt={starter.name} />
              <h3>{starter.name}</h3>
              <div className="types">
                {starter.types.map((type) => (
                  <span key={type} className={`type type-${type}`}>
                    {type}
                  </span>
                ))}
              </div>
              <div className="stats">
                <p><strong>HP:</strong> {starter.base_stats.hp}</p>
                <p><strong>Ataque:</strong> {starter.base_stats.attack}</p>
                <p><strong>Defensa:</strong> {starter.base_stats.defense}</p>
              </div>
            </div>
          ))}
        </div>

        {selectedStarter && (
          <div className="selected-starter-info">
            <h3>Has seleccionado a {selectedStarter.name}</h3>
            <p>Evoluciona a {selectedStarter.evolution.evolves_to} al nivel {selectedStarter.evolution.evolution_level}</p>
            <button 
              onClick={handleSelectStarter} 
              disabled={submitting}
              className="confirm-btn"
            >
              {submitting ? 'Confirmando...' : `¡Elegir a ${selectedStarter.name}!`}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default StarterSelection;