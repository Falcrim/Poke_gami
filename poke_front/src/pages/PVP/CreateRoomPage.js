import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { createRoom } from '../../services/pvpService';
import './CreateRoomPage.css';

const CreateRoomPage = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [roomData, setRoomData] = useState(null);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const createNewRoom = async () => {
      try {
        setCreating(true);
        setError('');
        
        const response = await createRoom();
        setRoomData(response);
        setLoading(false);
        setCreating(false);
        
      } catch (err) {
        setError('Error al crear la sala: ' + err.message);
        setLoading(false);
        setCreating(false);
        console.error('Error creating room:', err);
      }
    };

    createNewRoom();
  }, []);

  const handleCopyCode = () => {
    if (roomData?.room_code) {
      navigator.clipboard.writeText(roomData.room_code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleStartBattle = () => {
    if (roomData?.battle_id) {
      navigate(`/pvp-battle/${roomData.battle_id}`);
    }
  };

  const handleBack = () => {
    navigate('/dashboard');
  };

  if (loading) {
    return (
      <div className="create-room-container">
        <div className="loading-room">
          <div className="loading-spinner"></div>
          <p>{creating ? 'Creando sala...' : 'Cargando...'}</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="create-room-container">
        <div className="error-room">
          <h2>Error</h2>
          <p>{error}</p>
          <button onClick={handleBack}>Volver</button>
        </div>
      </div>
    );
  }

  return (
    <div className="create-room-container">
      <div className="room-waiting">
        <h2>🏠 Sala Creada</h2>
        
        <div className="room-info-card">
          <div className="room-code-section">
            <h3>Código de la Sala:</h3>
            <div className="room-code-display">
              <span className="code">{roomData.room_code}</span>
              <button 
                className={`copy-btn ${copied ? 'copied' : ''}`}
                onClick={handleCopyCode}
              >
                {copied ? '✓ Copiado' : '📋 Copiar'}
              </button>
            </div>
            <p className="code-instructions">
              Comparte este código con otro jugador para que se una
            </p>
          </div>

          <div className="room-details">
            <div className="detail-item">
              <span className="label">Formato:</span>
              <span className="value">{roomData.battle_format}</span>
            </div>
            <div className="detail-item">
              <span className="label">ID de Batalla:</span>
              <span className="value">#{roomData.battle_id}</span>
            </div>
            <div className="detail-item">
              <span className="label">Estado:</span>
              <span className="value status-waiting">Esperando jugador...</span>
            </div>
          </div>

          <div className="your-team-section">
            <h3>Tu Equipo Preparado:</h3>
            <div className="team-preview">
              {roomData.your_team.map((pokemon, index) => (
                <div key={index} className="pokemon-preview">
                  <img src={pokemon.sprite_front} alt={pokemon.pokemon_name} />
                  <div className="pokemon-info">
                    <span className="pokemon-name">{pokemon.pokemon_name}</span>
                    <span className="pokemon-level">Lv. {pokemon.level}</span>
                    <div className="pokemon-moves">
                      <small>Movimientos: {pokemon.total_moves}/4</small>
                      <small>Auto: {pokemon.auto_filled_moves}</small>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="waiting-message">
          <div className="waiting-animation">
            <div className="dot"></div>
            <div className="dot"></div>
            <div className="dot"></div>
          </div>
          <p>Esperando a que otro jugador se una...</p>
        </div>

        <div className="action-buttons">
          <button
            className="start-btn"
            onClick={handleStartBattle}
            disabled={roomData.state === 'waiting'}
          >
            {roomData.state === 'waiting' ? 'Esperando oponente...' : '¡Comenzar Batalla!'}
          </button>
          <button className="back-btn" onClick={handleBack}>
            Cancelar y Volver
          </button>
        </div>
      </div>
    </div>
  );
};

export default CreateRoomPage;