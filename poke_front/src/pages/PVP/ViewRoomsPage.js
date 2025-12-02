import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { getAvailableRooms, joinRoom, createRoom } from '../../services/pvpService';
import './ViewRoomsPage.css';

const ViewRoomsPage = () => {
  const navigate = useNavigate();
  const [rooms, setRooms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showJoinModal, setShowJoinModal] = useState(false);
  const [roomCode, setRoomCode] = useState('');
  const [joining, setJoining] = useState(false);
  const [creating, setCreating] = useState(false);
  const [isFetching, setIsFetching] = useState(false);
  const roomCodeInputRef = useRef(null);
  
  const refreshIntervalRef = useRef(null);
  const lastFetchTimeRef = useRef(0);
  const fetchCooldown = 5000;

  const fetchRooms = useCallback(async () => {
    if (isFetching) return;
    
    const now = Date.now();
    if (now - lastFetchTimeRef.current < fetchCooldown) {
      return;
    }
    
    try {
      setIsFetching(true);
      lastFetchTimeRef.current = now;
      
      const response = await getAvailableRooms();
      setRooms(response.rooms || []);
      setError('');
    } catch (err) {
      if (!err.message.includes('Failed to fetch')) {
        setError('Error al cargar salas disponibles');
      }
      console.error('Error fetching rooms:', err);
    } finally {
      setIsFetching(false);
      setLoading(false);
    }
  }, [isFetching]);

  useEffect(() => {
    fetchRooms();
    
    refreshIntervalRef.current = setInterval(fetchRooms, 30000);
    
    const handleVisibilityChange = () => {
      if (document.hidden) {
        if (refreshIntervalRef.current) {
          clearInterval(refreshIntervalRef.current);
          refreshIntervalRef.current = null;
        }
      } else {
        if (!refreshIntervalRef.current) {
          fetchRooms();
          refreshIntervalRef.current = setInterval(fetchRooms, 30000);
        }
      }
    };
    
    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    return () => {
      if (refreshIntervalRef.current) {
        clearInterval(refreshIntervalRef.current);
      }
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [fetchRooms]);

  const handleRefresh = useCallback(() => {
    const now = Date.now();
    if (now - lastFetchTimeRef.current < 2000) {
      return;
    }
    
    setLoading(true);
    fetchRooms();
  }, [fetchRooms]);

  const handleJoinRoom = async () => {
    if (!roomCode.trim()) {
      setError('Por favor ingresa un código de sala');
      return;
    }

    const codeRegex = /^[A-Z0-9]{6}$/;
    if (!codeRegex.test(roomCode.toUpperCase())) {
      setError('El código debe tener exactamente 6 caracteres alfanuméricos');
      return;
    }

    try {
      setJoining(true);
      setError('');
      
      const response = await joinRoom(roomCode.toUpperCase());
      
      if (response.battle_id) {
        if (refreshIntervalRef.current) {
          clearInterval(refreshIntervalRef.current);
          refreshIntervalRef.current = null;
        }
        navigate(`/pvp-battle/${response.battle_id}`);
      }
    } catch (err) {
      setError(err.message || 'Error al unirse a la sala');
      console.error('Error joining room:', err);
    } finally {
      setJoining(false);
    }
  };

  const handleBack = () => {
    if (refreshIntervalRef.current) {
      clearInterval(refreshIntervalRef.current);
    }
    navigate('/dashboard');
  };

  const handleCreateRoom = async () => {
    if (creating) return;
    
    try {
      setCreating(true);
      setError('');
      
      const response = await createRoom();
      
      if (response.battle_id) {
        if (refreshIntervalRef.current) {
          clearInterval(refreshIntervalRef.current);
          refreshIntervalRef.current = null;
        }
        navigate(`/pvp-battle/${response.battle_id}`);
      }
    } catch (err) {
      console.log('Full error:', err);
      console.log('Error data:', err.data);
      
      if (err.data && err.data.room_code) {
        navigate(`/create-room?resume=${err.data.room_code}`);
      } else {
        setError(err.message || 'Error al crear sala');
      }
    } finally {
      setCreating(false);
    }
  };

  const handleJoinSpecificRoom = (roomCodeFromCard) => {
    setRoomCode(roomCodeFromCard);
    handleJoinRoom();
  };

  const renderRoomCards = () => {
    if (!rooms || rooms.length === 0) {
      return (
        <div className="no-rooms">
          <div className="no-rooms-icon">🏠</div>
          <h3>No hay salas disponibles</h3>
          <p>Crea una nueva sala o espera a que alguien cree una</p>
          <button 
            className="create-room-btn" 
            onClick={handleCreateRoom}
            disabled={creating}
          >
            {creating ? 'Creando...' : 'Crear mi propia sala'}
          </button>
        </div>
      );
    }

    return (
      <div className="rooms-grid">
        {rooms.map((room) => (
          <div key={`${room.id}-${room.room_code}`} className="room-card">
            <div className="room-header">
              <span className="room-id">Sala #{room.id}</span>
              <span className={`room-status ${room.state}`}>
                {room.state === 'waiting' ? 'Esperando' : 'En curso'}
              </span>
            </div>
            
            <div className="room-body">
              <div className="room-code-display">
                <span className="code-label">Código:</span>
                <span className="code-value">{room.room_code}</span>
              </div>
              
              <div className="room-info">
                <div className="info-item">
                  <span className="label">Formato:</span>
                  <span className="value">{room.battle_format}</span>
                </div>
                <div className="info-item">
                  <span className="label">Creada por:</span>
                  <span className="value">{room.player1_username}</span>
                </div>
                <div className="info-item">
                  <span className="label">Creada:</span>
                  <span className="value">
                    {new Date(room.created_at).toLocaleTimeString([], { 
                      hour: '2-digit', 
                      minute: '2-digit' 
                    })}
                  </span>
                </div>
              </div>
              
              <button 
                className="join-btn"
                onClick={() => handleJoinSpecificRoom(room.room_code)}
                disabled={room.state !== 'waiting' || joining}
                title={room.state !== 'waiting' ? 'Sala en curso, no se puede unir' : ''}
              >
                {room.state !== 'waiting' ? 'En curso' : 'Unirse'}
              </button>
            </div>
          </div>
        ))}
      </div>
    );
  };

  if (loading && rooms.length === 0) {
    return (
      <div className="view-rooms-container">
        <div className="loading-rooms">
          <div className="loading-spinner"></div>
          <p>Cargando salas disponibles...</p>
          {isFetching && <p className="fetching-indicator">Actualizando...</p>}
        </div>
      </div>
    );
  }

  return (
    <div className="view-rooms-container">
      <div className="rooms-header">
        <h2>🎮 Salas de Batalla PvP</h2>
        <div className="header-actions">
          <button 
            className="refresh-btn" 
            onClick={handleRefresh}
            disabled={isFetching}
            title={isFetching ? 'Actualizando...' : 'Actualizar lista'}
          >
            {isFetching ? '🔄 Actualizando...' : '🔄 Actualizar'}
          </button>
          <button 
            className="create-room-btn"
            onClick={handleCreateRoom}
            disabled={creating}
          >
            {creating ? 'Creando...' : '➕ Crear Nueva Sala'}
          </button>
        </div>
      </div>

      {error && (
        <div className="error-message">
          {error}
          <button className="dismiss-error" onClick={() => setError('')}>×</button>
        </div>
      )}

      <div className="rooms-content">
        {renderRoomCards()}

        <div className="join-section">
          <div className="join-card">
            <h3>¿Tienes un código de sala?</h3>
            <p>Ingresa el código que te compartieron para unirte directamente</p>
            <div className="code-input-group">
              <input
                ref={roomCodeInputRef}
                type="text"
                placeholder="Ej: DFCDH8"
                value={roomCode}
                onChange={(e) => {
                  const value = e.target.value.toUpperCase().replace(/[^A-Z0-9]/g, '');
                  setRoomCode(value.slice(0, 6));
                }}
                maxLength={6}
                className="code-input"
                disabled={joining}
              />
              <button
                className="join-direct-btn"
                onClick={handleJoinRoom}
                disabled={joining || !roomCode.trim() || roomCode.length !== 6}
                title={roomCode.length !== 6 ? 'El código debe tener 6 caracteres' : ''}
              >
                {joining ? 'Uniéndose...' : 'Unirse con Código'}
              </button>
            </div>
            <div className="code-hint">
              <small>Ingresa exactamente 6 caracteres (A-Z, 0-9)</small>
            </div>
          </div>
        </div>
      </div>

      <button className="back-btn" onClick={handleBack}>
        ← Volver al Dashboard
      </button>

      {showJoinModal && (
        <div className="modal-overlay" onClick={() => setShowJoinModal(false)}>
          <div className="join-modal" onClick={(e) => e.stopPropagation()}>
            <h3>Unirse a Sala</h3>
            <p>Ingresa el código de 6 caracteres de la sala:</p>
            
            <div className="modal-input-group">
              <input
                type="text"
                placeholder="ABCDEF"
                value={roomCode}
                onChange={(e) => {
                  const value = e.target.value.toUpperCase().replace(/[^A-Z0-9]/g, '');
                  setRoomCode(value.slice(0, 6));
                }}
                maxLength={6}
                className="modal-code-input"
                autoFocus
                disabled={joining}
              />
            </div>
            
            {error && (
              <div className="modal-error">
                {error}
                <button className="dismiss-modal-error" onClick={() => setError('')}>×</button>
              </div>
            )}
            
            <div className="modal-buttons">
              <button
                className="modal-join-btn"
                onClick={handleJoinRoom}
                disabled={joining || !roomCode.trim() || roomCode.length !== 6}
              >
                {joining ? 'Uniéndose...' : 'Unirse'}
              </button>
              <button
                className="modal-cancel-btn"
                onClick={() => {
                  setShowJoinModal(false);
                  setError('');
                }}
                disabled={joining}
              >
                Cancelar
              </button>
            </div>
            
            <div className="modal-footer">
              <small>Presiona ESC o haz clic fuera para cancelar</small>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ViewRoomsPage;