import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { closeRoom } from '../../services/pvpService';
import './CreateRoomPage.css';

const CreateRoomPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [loading, setLoading] = useState(false);
  const [roomData, setRoomData] = useState(null);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const queryParams = new URLSearchParams(location.search);
    const resumeCode = queryParams.get('resume');
    
    if (resumeCode) {
      setRoomData({
        room_code: resumeCode,
        battle_id: 0,
        battle_format: "1vs1",
        state: "waiting"
      });
    } else {
      setError('No se pudo cargar la información de la sala');
    }
  }, [location]);

  const handleCopyCode = () => {
    if (roomData?.room_code) {
      navigator.clipboard.writeText(roomData.room_code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleStartBattle = () => {
    if (roomData?.room_code) {
      navigate(`/pvp-battle/${roomData.room_code}`);
    }
  };

  const handleCloseRoom = async () => {
    if (!roomData?.room_code) return;
    
    try {
      setLoading(true);
      await closeRoom(roomData.room_code);
      navigate('/dashboard');
    } catch (err) {
      setError('Error al cerrar la sala: ' + err.message);
      setLoading(false);
    }
  };

  const handleBack = () => {
    navigate('/dashboard');
  };

  if (error && !roomData) {
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

  if (!roomData) {
    return (
      <div className="create-room-container">
        <div className="loading-room">
          <div className="loading-spinner"></div>
          <p>Cargando información de la sala...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="create-room-container" style={{ color: '#000000' }}>
      <div className="room-waiting">
        <h2 style={{ color: '#000000' }}>🏠 Tu Sala Activa</h2>
        
        <div className="room-info-card" style={{ color: '#000000' }}>
          <div className="room-code-section">
            <h3 style={{ color: '#000000' }}>Código de la Sala:</h3>
            <div className="room-code-display">
              <span className="code">{roomData.room_code}</span>
              <button 
                className={`copy-btn ${copied ? 'copied' : ''}`}
                onClick={handleCopyCode}
              >
                {copied ? '✓ Copiado' : '📋 Copiar'}
              </button>
            </div>
            <p className="code-instructions" style={{ color: '#000000' }}>
              Comparte este código con otro jugador para que se una
            </p>
          </div>

          <div className="room-details">
            <div className="detail-item" style={{ color: '#000000' }}>
              <span className="label" style={{ color: '#000000' }}>Formato:</span>
              <span className="value" style={{ color: '#000000' }}>{roomData.battle_format}</span>
            </div>
            <div className="detail-item" style={{ color: '#000000' }}>
              <span className="label" style={{ color: '#000000' }}>Código:</span>
              <span className="value" style={{ color: '#000000' }}>{roomData.room_code}</span>
            </div>
            <div className="detail-item" style={{ color: '#000000' }}>
              <span className="label" style={{ color: '#000000' }}>Estado:</span>
              <span className="value status-waiting">Esperando jugador...</span>
            </div>
          </div>
        </div>

        <div className="waiting-message" style={{ color: '#000000' }}>
          <div className="waiting-animation">
            <div className="dot"></div>
            <div className="dot"></div>
            <div className="dot"></div>
          </div>
          <p style={{ color: '#000000' }}>Esperando a que otro jugador se una...</p>
        </div>

        <div className="action-buttons">
          <button
            className="start-btn"
            onClick={handleStartBattle}
            disabled={roomData.state === 'waiting'}
          >
            {roomData.state === 'waiting' ? 'Esperando oponente...' : '¡Comenzar Batalla!'}
          </button>
          <button 
            className="close-btn"
            onClick={handleCloseRoom}
            disabled={loading}
          >
            {loading ? 'Cerrando...' : 'Cerrar Sala'}
          </button>
          <button className="back-btn" onClick={handleBack}>
            Volver al Dashboard
          </button>
        </div>
      </div>
    </div>
  );
};

export default CreateRoomPage;