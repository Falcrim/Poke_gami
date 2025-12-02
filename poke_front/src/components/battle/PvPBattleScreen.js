import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getBattleState, pvpAttack, pvpSurrender } from '../../services/pvpService';
import './PvPBattleScreen.css';

const PvPBattleScreen = () => {
  const { battleId } = useParams();
  const navigate = useNavigate();

  // Estados principales
  const [battleData, setBattleData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [battleLog, setBattleLog] = useState([]);
  const [showMoveMenu, setShowMoveMenu] = useState(false);
  const [actionInProgress, setActionInProgress] = useState(false);
  const [battleEnded, setBattleEnded] = useState(false);
  const [showSurrenderModal, setShowSurrenderModal] = useState(false);

  // Estados para animaciones
  const [enemyShaking, setEnemyShaking] = useState(false);
  const [playerShaking, setPlayerShaking] = useState(false);
  const [playerAttacking, setPlayerAttacking] = useState(false);
  const [enemyAttacking, setEnemyAttacking] = useState(false);
  const [damageEffect, setDamageEffect] = useState(null);
  const [showEffectiveness, setShowEffectiveness] = useState('');

  // HP animados
  const [enemyHP, setEnemyHP] = useState(0);
  const [playerHP, setPlayerHP] = useState(0);
  const [enemyMaxHP, setEnemyMaxHP] = useState(0);
  const [playerMaxHP, setPlayerMaxHP] = useState(0);

  // Sprites
  const [currentEnemySprite, setCurrentEnemySprite] = useState('');
  const [currentPlayerSprite, setCurrentPlayerSprite] = useState('');

  // Datos actuales
  const [currentPlayerPokemon, setCurrentPlayerPokemon] = useState(null);
  const [currentOpponentPokemon, setCurrentOpponentPokemon] = useState(null);

  // Referencias para animaciones
  const enemyHPRef = useRef(0);
  const playerHPRef = useRef(0);

  // Polling interval
  const [pollInterval, setPollInterval] = useState(null);
  const lastUpdateRef = useRef(Date.now());

  // Encontrar Pokémon actual
  const findCurrentPokemon = (team, currentIndex) => {
    if (!team || team.length === 0) return null;
    return team[currentIndex] || team[0];
  };

  // Cargar estado de batalla
  const loadBattleState = async () => {
    try {
      const response = await getBattleState(battleId);
      
      // Evitar actualizaciones demasiado frecuentes
      const now = Date.now();
      if (now - lastUpdateRef.current < 1000) return;
      lastUpdateRef.current = now;
      
      setBattleData(response);
      
      // Actualizar sprites y HP del jugador
      const playerPokemon = findCurrentPokemon(
        response.your_team, 
        response.your_current_pokemon_index
      );
      
      if (playerPokemon) {
        setCurrentPlayerPokemon(playerPokemon);
        setCurrentPlayerSprite(playerPokemon.sprite_back || 
          `https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/back/${playerPokemon.pokemon_id || 1}.png`);
        
        setPlayerHP(playerPokemon.current_hp);
        setPlayerMaxHP(playerPokemon.max_hp);
        playerHPRef.current = playerPokemon.current_hp;
      }
      
      // Actualizar sprites y HP del oponente
      const opponentPokemon = findCurrentPokemon(
        response.opponent_team, 
        response.opponent_current_pokemon_index
      );
      
      if (opponentPokemon) {
        setCurrentOpponentPokemon(opponentPokemon);
        setCurrentEnemySprite(opponentPokemon.sprite_front || 
          `https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/${opponentPokemon.pokemon_id || 1}.png`);
        
        setEnemyHP(opponentPokemon.current_hp);
        setEnemyMaxHP(opponentPokemon.max_hp);
        enemyHPRef.current = opponentPokemon.current_hp;
      }
      
      // Verificar si la batalla terminó
      if (response.state === 'finished' || response.winner_username) {
        setBattleEnded(true);
        if (pollInterval) {
          clearInterval(pollInterval);
          setPollInterval(null);
        }
        
        // Agregar mensaje de fin de batalla al log
        if (response.winner_username) {
          addToBattleLog(`¡${response.winner_username} ha ganado la batalla!`);
        }
      }
      
      setLoading(false);
    } catch (err) {
      setError('Error al cargar estado de batalla: ' + err.message);
      setLoading(false);
      console.error('Error loading battle state:', err);
    }
  };

  // Inicializar batalla
  useEffect(() => {
    loadBattleState();
    
    // Configurar polling cada 2 segundos
    const interval = setInterval(loadBattleState, 2000);
    setPollInterval(interval);
    
    return () => {
      if (pollInterval) clearInterval(pollInterval);
    };
  }, [battleId]);

  // Función auxiliar para agregar mensajes al log
  const addToBattleLog = (message) => {
    setBattleLog(prev => {
      const newLog = [...prev, message];
      return newLog.slice(-4);
    });
  };

  // Animación suave de cambio de HP
  const animateHPChange = (target, newHP, maxHP) => {
    return new Promise((resolve) => {
      const steps = 20;
      const delay = 30;

      if (target === 'enemy') {
        const current = enemyHPRef.current;
        const step = (newHP - current) / steps;

        for (let i = 1; i <= steps; i++) {
          setTimeout(() => {
            const newValue = current + (step * i);
            setEnemyHP(Math.max(0, Math.min(Math.round(newValue), maxHP)));
            enemyHPRef.current = newValue;
            
            if (i === steps) resolve();
          }, i * delay);
        }
      } else {
        const current = playerHPRef.current;
        const step = (newHP - current) / steps;

        for (let i = 1; i <= steps; i++) {
          setTimeout(() => {
            const newValue = current + (step * i);
            setPlayerHP(Math.max(0, Math.min(Math.round(newValue), maxHP)));
            playerHPRef.current = newValue;
            
            if (i === steps) resolve();
          }, i * delay);
        }
      }
    });
  };

  // Función para atacar
  const handleAttack = async (move) => {
    if (actionInProgress || !battleData || !move || !battleData.your_turn) return;

    setActionInProgress(true);
    setShowMoveMenu(false);

    try {
      addToBattleLog(`${currentPlayerPokemon?.pokemon_name} usó ${move.name}!`);

      // Animación de ataque
      setPlayerAttacking(true);
      setTimeout(() => setPlayerAttacking(false), 300);

      setDamageEffect('player-attack');
      setTimeout(() => {
        setDamageEffect(null);
        setEnemyShaking(true);
        setTimeout(() => setEnemyShaking(false), 500);
      }, 200);

      const response = await pvpAttack(battleId, move.id);

      // Actualizar HP si hay daño
      if (response.damage && response.battle_state) {
        const opponentPokemon = findCurrentPokemon(
          response.battle_state.opponent_team,
          response.battle_state.opponent_current_pokemon_index
        );
        
        if (opponentPokemon) {
          await animateHPChange('enemy', opponentPokemon.current_hp, opponentPokemon.max_hp);
        }
      }

      addToBattleLog(response.message);

      // Recargar estado para actualizar turno
      setTimeout(() => {
        loadBattleState();
        setActionInProgress(false);
      }, 1500);

    } catch (err) {
      setError('Error al atacar: ' + err.message);
      setActionInProgress(false);
    }
  };

  // Función para rendirse
  const handleSurrender = async () => {
    if (actionInProgress) return;

    setShowSurrenderModal(false);
    setActionInProgress(true);

    try {
      await pvpSurrender(battleId);
      addToBattleLog('¡Te has rendido!');
      setBattleEnded(true);
      
      setTimeout(() => {
        navigate('/dashboard');
      }, 3000);

    } catch (err) {
      setError('Error al rendirse: ' + err.message);
      setActionInProgress(false);
    }
  };

  // Renderizar barra de HP
  const renderHPBar = (currentHP, maxHP, isEnemy = false) => {
    const percentage = Math.max(0, Math.min(100, (currentHP / maxHP) * 100));
    let color;

    if (percentage > 50) color = '#27ae60';
    else if (percentage > 20) color = '#f39c12';
    else color = '#e74c3c';

    return (
      <div className={`hp-bar ${isEnemy ? 'enemy-hp-bar' : 'player-hp-bar'}`}>
        <div className="hp-info">
          <span className="hp-label">PS</span>
          <span className="hp-numbers">{Math.round(currentHP)}/{maxHP}</span>
        </div>
        <div className="hp-bar-container">
          <div
            className="hp-bar-fill"
            style={{
              width: `${percentage}%`,
              backgroundColor: color,
              transition: 'width 0.8s cubic-bezier(0.34, 1.56, 0.64, 1)'
            }}
          ></div>
        </div>
      </div>
    );
  };

  // Renderizar menú de movimientos
  const renderMoveMenu = () => {
    if (!currentPlayerPokemon?.moves) return null;

    return (
      <div className="move-menu-overlay">
        <div className="move-menu">
          <h3>Elige un movimiento</h3>
          <div className="move-grid">
            {currentPlayerPokemon.moves.map((move, index) => (
              <div key={move.id || index} className="move-option">
                <button
                  className="move-button"
                  onClick={() => handleAttack(move)}
                  disabled={actionInProgress || !battleData?.your_turn}
                  title={!battleData?.your_turn ? 'No es tu turno' : ''}
                >
                  <span className="move-name">{move.name}</span>
                  <span className="move-pp">
                    PP: {move.current_pp}/{move.pp}
                  </span>
                  <span className="move-power">
                    {move.power > 0 ? `Poder: ${move.power}` : 'Estado'}
                  </span>
                  <span className="move-accuracy">
                    Prec: {move.accuracy}%
                  </span>
                </button>
              </div>
            ))}
          </div>
          <button
            className="back-button"
            onClick={() => setShowMoveMenu(false)}
            disabled={actionInProgress}
          >
            Atrás
          </button>
        </div>
      </div>
    );
  };

  // Renderizar información de oponente
  const renderOpponentInfo = () => {
    if (!battleData) return null;

    const opponentUsername = battleData.player1_username === battleData.current_turn_username 
      ? battleData.player1_username 
      : battleData.player2_username;

    return (
      <div className="opponent-info">
        <div className="opponent-username">
          <span className="label">Oponente:</span>
          <span className="value">{opponentUsername}</span>
        </div>
        <div className="turn-indicator">
          <span className={`turn-badge ${battleData.your_turn ? 'your-turn' : 'opponent-turn'}`}>
            {battleData.your_turn ? '¡TU TURNO!' : 'Turno del oponente'}
          </span>
        </div>
        <div className="room-code">
          <span className="label">Sala:</span>
          <span className="value">{battleData.room_code}</span>
        </div>
      </div>
    );
  };

  // Si la batalla terminó
  if (battleEnded) {
    const winner = battleData?.winner_username;
    const currentUsername = battleData?.player1_username === battleData?.current_turn_username 
      ? battleData.player1_username 
      : battleData.player2_username;
    const isWinner = winner === currentUsername;
    
    return (
      <div className="battle-ended">
        <h2>Batalla PvP Terminada</h2>
        <div className="result-message">
          <h3>{winner ? `¡${winner} ha ganado!` : 'Batalla finalizada'}</h3>
          {winner && (
            <p className={isWinner ? 'victory-text' : 'defeat-text'}>
              {isWinner ? '¡Has ganado la batalla!' : '¡Has perdido la batalla!'}
            </p>
          )}
        </div>
        <button 
          className="return-btn"
          onClick={() => navigate('/dashboard')}
        >
          Volver al Dashboard
        </button>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="battle-loading">
        <div className="battle-spinner"></div>
        <p>Cargando batalla PvP...</p>
        <p className="loading-subtext">Esperando conexión con el oponente</p>
      </div>
    );
  }

  if (error || !battleData) {
    return (
      <div className="battle-error">
        <h2>Error en la batalla PvP</h2>
        <p>{error || 'No se pudo cargar la batalla'}</p>
        <button 
          className="return-btn"
          onClick={() => navigate('/dashboard')}
        >
          Volver al Dashboard
        </button>
      </div>
    );
  }

  // Verificar si la batalla está en estado de espera
  if (battleData.state === 'waiting') {
    return (
      <div className="waiting-for-opponent">
        <div className="waiting-content">
          <h2>Esperando al oponente...</h2>
          <div className="loading-animation">
            <div className="loading-dot"></div>
            <div className="loading-dot"></div>
            <div className="loading-dot"></div>
          </div>
          <p className="room-info">
            Sala: <strong>{battleData.room_code}</strong>
          </p>
          <p className="waiting-instruction">
            Comparte el código con otro jugador para comenzar
          </p>
          <button 
            className="cancel-btn"
            onClick={() => navigate('/dashboard')}
          >
            Cancelar y volver
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="pvp-battle-screen">
      <div className="battle-background">
        {/* Información del oponente */}
        {renderOpponentInfo()}

        {/* Pokémon Oponente */}
        <div className="enemy-container">
          <div className={`enemy-sprite ${enemyShaking ? 'shaking' : ''} ${enemyAttacking ? 'attacking' : ''}`}>
            <img
              src={currentEnemySprite}
              alt={currentOpponentPokemon?.pokemon_name || 'Oponente'}
              onError={(e) => {
                e.target.onerror = null;
                e.target.src = 'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/1.png';
              }}
            />
          </div>

          <div className="enemy-info-panel">
            <div className="enemy-name">
              {currentOpponentPokemon?.pokemon_name || 'Pokémon oponente'}
              <span className="enemy-level">
                Lv.{currentOpponentPokemon?.level || 1}
              </span>
            </div>
            {renderHPBar(enemyHP, enemyMaxHP, true)}
          </div>
        </div>

        {/* Pokémon del Jugador */}
        <div className="player-container">
          <div className={`player-sprite ${playerShaking ? 'shaking' : ''} ${playerAttacking ? 'attacking' : ''}`}>
            <img
              src={currentPlayerSprite}
              alt={currentPlayerPokemon?.pokemon_name || 'Tu Pokémon'}
              onError={(e) => {
                e.target.onerror = null;
                e.target.src = 'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/back/1.png';
              }}
            />
          </div>

          <div className="player-info-panel">
            <div className="player-name">
              {currentPlayerPokemon?.pokemon_name || 'Tu Pokémon'}
              <span className="player-level">Lv.{currentPlayerPokemon?.level || 1}</span>
            </div>
            {renderHPBar(playerHP, playerMaxHP, false)}
            
            {/* Movimientos disponibles */}
            <div className="moves-quickview">
              {currentPlayerPokemon?.moves?.slice(0, 2).map((move, index) => (
                <div key={index} className="move-quick">
                  <span className="move-name-quick">{move.name}</span>
                  <span className="move-pp-quick">{move.current_pp}/{move.pp}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Logs del combate */}
        <div className="battle-log-panel">
          <div className="battle-logs">
            {battleLog.length > 0 ? (
              battleLog.map((message, index) => (
                <p key={index}>{message}</p>
              ))
            ) : (
              <p>La batalla ha comenzado. ¡Buena suerte!</p>
            )}
          </div>
        </div>

        {/* Menú de acciones (Solo LUCHAR y RENDIRSE) */}
        <div className="action-panel">
          <div className="action-buttons">
            <div className="action-row">
              <button
                className="action-button fight"
                onClick={() => setShowMoveMenu(true)}
                disabled={actionInProgress || !battleData.your_turn || battleData.state !== 'active'}
                title={!battleData.your_turn ? 'No es tu turno' : ''}
              >
                LUCHAR
              </button>
              <button
                className="action-button surrender"
                onClick={() => setShowSurrenderModal(true)}
                disabled={actionInProgress || battleData.state !== 'active'}
              >
                RENDIRSE
              </button>
            </div>
          </div>
        </div>

        {showEffectiveness && (
          <div className="effectiveness-message">{showEffectiveness}</div>
        )}
        
        {damageEffect && (
          <div className={`damage-effect ${damageEffect}`}></div>
        )}
      </div>

      {showMoveMenu && renderMoveMenu()}

      <button
        className="back-to-dashboard"
        onClick={() => navigate('/dashboard')}
        disabled={actionInProgress}
      >
        ← Volver al Dashboard
      </button>

      {/* Modal de rendición */}
      {showSurrenderModal && (
        <div className="modal-overlay" onClick={() => setShowSurrenderModal(false)}>
          <div className="surrender-modal" onClick={(e) => e.stopPropagation()}>
            <h3>⚠️ Confirmar Rendición</h3>
            <p>¿Estás seguro de que quieres rendirte?</p>
            <p className="warning-text">Esta acción dará la victoria automática a tu oponente</p>
            
            <div className="modal-buttons">
              <button
                className="confirm-surrender-btn"
                onClick={handleSurrender}
                disabled={actionInProgress}
              >
                {actionInProgress ? 'Rindiéndose...' : 'Sí, rendirse'}
              </button>
              <button
                className="cancel-surrender-btn"
                onClick={() => setShowSurrenderModal(false)}
                disabled={actionInProgress}
              >
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PvPBattleScreen;