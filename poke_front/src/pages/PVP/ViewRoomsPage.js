import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { getAvailableRooms, joinRoom } from '../../services/pvpService';
import './ViewRoomsPage.css';

const ViewRoomsPage = () => {
  const navigate = useNavigate();
  const [rooms, setRooms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showJoinModal, setShowJoinModal] = useState(false);
  const [roomCode, setRoomCode] = useState('');
  const [joining, setJoining] = useState(false);
  const [isFetching, setIsFetching] = useState(false);
  const roomCodeInputRef = useRef(null);
  
  // Usar useRef para el intervalo (mejor práctica)
  const refreshIntervalRef = useRef(null);
  const lastFetchTimeRef = useRef(0);
  const fetchCooldown = 5000; // 5 segundos entre peticiones

  // Función optimizada para fetchRooms
  const fetchRooms = useCallback(async () => {
    // Evitar múltiples peticiones simultáneas
    if (isFetching) return;
    
    // Cooldown para evitar peticiones demasiado frecuentes
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
      // Solo mostrar error si no es un error de red
      if (!err.message.includes('Failed to fetch')) {
        setError('Error al cargar salas disponibles');
      }
      console.error('Error fetching rooms:', err);
    } finally {
      setIsFetching(false);
      setLoading(false);
    }
  }, [isFetching]);

  // Efecto para inicializar y manejar polling
  useEffect(() => {
    // Fetch inicial
    fetchRooms();
    
    // Configurar actualización automática cada 30 segundos (en lugar de 10)
    refreshIntervalRef.current = setInterval(fetchRooms, 30000);
    
    // Función para manejar visibilidad de pestaña
    const handleVisibilityChange = () => {
      if (document.hidden) {
        // Pausar polling cuando la pestaña no está activa
        if (refreshIntervalRef.current) {
          clearInterval(refreshIntervalRef.current);
          refreshIntervalRef.current = null;
        }
      } else {
        // Reanudar polling cuando la pestaña vuelve a estar activa
        if (!refreshIntervalRef.current) {
          fetchRooms(); // Fetch inmediato al volver
          refreshIntervalRef.current = setInterval(fetchRooms, 30000);
        }
      }
    };
    
    // Escuchar cambios de visibilidad
    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    // Cleanup
    return () => {
      if (refreshIntervalRef.current) {
        clearInterval(refreshIntervalRef.current);
      }
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [fetchRooms]);

  // Función para refresh manual con cooldown
  const handleRefresh = useCallback(() => {
    const now = Date.now();
    if (now - lastFetchTimeRef.current < 2000) { // 2 segundos cooldown para refresh manual
      return;
    }
    
    setLoading(true);
    fetchRooms();
  }, [fetchRooms]);

  const handleJoinClick = () => {
    setShowJoinModal(true);
    setTimeout(() => {
      if (roomCodeInputRef.current) {
        roomCodeInputRef.current.focus();
      }
    }, 100);
  };

  const handleJoinRoom = async () => {
    if (!roomCode.trim()) {
      setError('Por favor ingresa un código de sala');
      return;
    }

    // Validar formato del código (6 caracteres alfanuméricos)
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
        // Detener polling antes de navegar
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
    // Limpiar intervalo antes de navegar
    if (refreshIntervalRef.current) {
      clearInterval(refreshIntervalRef.current);
    }
    navigate('/dashboard');
  };

  const handleCreateRoom = () => {
    // Limpiar intervalo antes de navegar
    if (refreshIntervalRef.current) {
      clearInterval(refreshIntervalRef.current);
    }
    navigate('/create-room');
  };

  // Función para unirse a una sala específica desde la tarjeta
  const handleJoinSpecificRoom = (roomCodeFromCard) => {
    setRoomCode(roomCodeFromCard);
    handleJoinRoom();
  };

  // Renderizar tarjetas de sala optimizadas
  const renderRoomCards = () => {
    if (!rooms || rooms.length === 0) {
      return (
        <div className="no-rooms">
          <div className="no-rooms-icon">🏠</div>
          <h3>No hay salas disponibles</h3>
          <p>Crea una nueva sala o espera a que alguien cree una</p>
          <button className="create-room-btn" onClick={handleCreateRoom}>
            Crear mi propia sala
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
          <button className="create-room-btn" onClick={handleCreateRoom}>
            ➕ Crear Nueva Sala
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

      {/* Modal de unirse */}
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