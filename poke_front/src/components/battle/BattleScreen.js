// components/battle/BattleScreen.js
import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  startWildBattle,
  startTrainerBattle,
  attackPokemon,
  battleUseItem,
  switchPokemon,
  fleeBattle
} from '../../services/battleService';
import {
  getBag,
  getTeamOrder
} from '../../services/gameService';
import './BattleScreen.css';

const BattleScreen = () => {
  const { battleType } = useParams();
  const navigate = useNavigate();

  // Estados principales
  const [battleData, setBattleData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [battleLog, setBattleLog] = useState([]);
  const [showMoveMenu, setShowMoveMenu] = useState(false);
  const [showBagMenu, setShowBagMenu] = useState(false);
  const [showPokemonMenu, setShowPokemonMenu] = useState(false);
  const [bagItems, setBagItems] = useState(null);
  const [playerTeam, setPlayerTeam] = useState([]);
  const [actionInProgress, setActionInProgress] = useState(false);
  const [battleEnded, setBattleEnded] = useState(false);

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

  // Sprites que se mantienen
  const [currentEnemySprite, setCurrentEnemySprite] = useState('');
  const [currentPlayerSprite, setCurrentPlayerSprite] = useState('');

  // Datos del Pokémon actual del jugador
  const [currentPlayerPokemon, setCurrentPlayerPokemon] = useState(null);

  // Datos del entrenador (solo para combate trainer)
  const [trainerData, setTrainerData] = useState(null);

  // Referencias para animaciones
  const enemyHPRef = useRef(0);
  const playerHPRef = useRef(0);

  // Estado para notificación de captura
  const [captureNotification, setCaptureNotification] = useState(null);

  // Función para obtener nombre del item
  const getItemName = (itemType) => {
    switch (itemType) {
      case 'pokeball': return 'Pokéball';
      case 'ultra_ball': return 'Ultraball';
      case 'potion': return 'Poción';
      case 'super_potion': return 'Superpoción';
      case 'hyper_potion': return 'Hiperpoción';
      default: return itemType;
    }
  };

  // Encontrar Pokémon actual en el equipo
  const findCurrentPlayerPokemon = (team, battleData) => {
    if (!team || !battleData?.player_pokemon) return null;
    return team.find(p => p.id === battleData.player_pokemon.id) || team[0];
  };

  // Iniciar combate
  useEffect(() => {
    const initBattle = async () => {
      try {
        setLoading(true);
        setError('');
        setBattleEnded(false);
        setCaptureNotification(null);
        setTrainerData(null);

        // Obtener equipo primero
        const teamData = await getTeamOrder();
        setPlayerTeam(teamData.team);

        // Iniciar combate según el tipo
        if (battleType === 'wild') {
          const battleResponse = await startWildBattle();
          setBattleData(battleResponse);

          // Encontrar Pokémon actual del jugador
          const currentPokemon = findCurrentPlayerPokemon(teamData.team, battleResponse);
          setCurrentPlayerPokemon(currentPokemon);

          // Establecer sprites
          if (battleResponse.wild_pokemon?.sprite_front) {
            setCurrentEnemySprite(battleResponse.wild_pokemon.sprite_front);
          }
          if (currentPokemon?.sprite_back) {
            setCurrentPlayerSprite(currentPokemon.sprite_back);
          }

          // Inicializar HP
          setEnemyHP(battleResponse.wild_pokemon.current_hp);
          setPlayerHP(battleResponse.player_pokemon.current_hp);
          setEnemyMaxHP(battleResponse.wild_pokemon.max_hp || battleResponse.wild_pokemon.hp);
          setPlayerMaxHP(battleResponse.player_pokemon.max_hp || battleResponse.player_pokemon.hp);

          enemyHPRef.current = battleResponse.wild_pokemon.current_hp;
          playerHPRef.current = battleResponse.player_pokemon.current_hp;

          setBattleLog([battleResponse.message]);

        } else if (battleType === 'trainer') {
          const battleResponse = await startTrainerBattle();
          setBattleData(battleResponse);
          setTrainerData(battleResponse.trainer);

          // Encontrar Pokémon actual del jugador
          const currentPokemon = findCurrentPlayerPokemon(teamData.team, battleResponse);
          setCurrentPlayerPokemon(currentPokemon);

          // Establecer sprites
          if (battleResponse.opponent_pokemon?.sprite_front) {
            setCurrentEnemySprite(battleResponse.opponent_pokemon.sprite_front);
          }
          if (currentPokemon?.sprite_back) {
            setCurrentPlayerSprite(currentPokemon.sprite_back);
          }

          // Inicializar HP
          setEnemyHP(battleResponse.opponent_pokemon.current_hp);
          setPlayerHP(battleResponse.player_pokemon.current_hp);
          setEnemyMaxHP(battleResponse.opponent_pokemon.max_hp || battleResponse.opponent_pokemon.hp);
          setPlayerMaxHP(battleResponse.player_pokemon.max_hp || battleResponse.player_pokemon.hp);

          enemyHPRef.current = battleResponse.opponent_pokemon.current_hp;
          playerHPRef.current = battleResponse.player_pokemon.current_hp;

          setBattleLog([battleResponse.message]);
        }

        // Obtener mochila (solo para combate salvaje)
        if (battleType === 'wild') {
          const bagData = await getBag();
          setBagItems(bagData[0]);
        } else {
          setBagItems({}); // Mochila vacía para combate trainer
        }

      } catch (err) {
        setError('Error al iniciar el combate: ' + err.message);
        console.error('Error:', err);
      } finally {
        setLoading(false);
      }
    };

    initBattle();
  }, [battleType]);

  // Función auxiliar para agregar mensajes al log
  const addToBattleLog = (message) => {
    setBattleLog(prev => {
      const newLog = [...prev, message];
      return newLog.slice(-2);
    });
  };

  // Animación suave de cambio de HP
  const animateHPChange = (target, newHP, maxHP) => {
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
        }, i * delay);
      }
    }
  };

  // Función para actualizar datos del combate
  const updateBattleData = (newBattleData) => {
    setBattleData(newBattleData);

    // Si cambia el Pokémon del jugador, actualizar sus datos
    if (newBattleData?.player_pokemon) {
      const newCurrentPokemon = findCurrentPlayerPokemon(playerTeam, newBattleData);
      if (newCurrentPokemon && newCurrentPokemon.id !== currentPlayerPokemon?.id) {
        setCurrentPlayerPokemon(newCurrentPokemon);
        if (newCurrentPokemon.sprite_back) {
          setCurrentPlayerSprite(newCurrentPokemon.sprite_back);
        }
      }
    }
  };

  // Función para atacar (funciona para ambos tipos)
  // Modifica la función handleAttack (la parte donde actualizas los datos después del ataque):
const handleAttack = async (move) => {
  if (actionInProgress || !battleData || !move) return;

  setActionInProgress(true);
  setShowMoveMenu(false);

  try {
    const enemyName = battleType === 'wild'
      ? battleData.wild_pokemon?.name
      : battleData.opponent_pokemon?.pokemon_name;

    addToBattleLog(`${battleData.player_pokemon.name} usó ${move.name}!`);

    // Animación de ataque
    setPlayerAttacking(true);
    setTimeout(() => setPlayerAttacking(false), 300);

    setDamageEffect('player-attack');
    setTimeout(() => {
      setDamageEffect(null);
      setEnemyShaking(true);
      setTimeout(() => setEnemyShaking(false), 500);
    }, 200);

    const response = await attackPokemon(battleData.battle_id, move.id);

    // ACTUALIZACIÓN CRÍTICA: Si el Pokémon rival cambió (combate trainer)
    let opponentPokemonChanged = false;
    if (battleType === 'trainer' && response.battle_state) {
      const newOpponentId = response.battle_state.opponent_pokemon?.id;
      const currentOpponentId = battleData.opponent_pokemon?.id;
      
      if (newOpponentId && newOpponentId !== currentOpponentId) {
        opponentPokemonChanged = true;
        console.log('¡El entrenador ha cambiado de Pokémon!');
      }
    }

    // Actualizar HP con animación
    if (response.battle_state) {
      const enemyHPData = battleType === 'wild'
        ? response.battle_state.wild_pokemon.current_hp
        : response.battle_state.opponent_pokemon.current_hp;

      const playerHPData = response.battle_state.player_pokemon.current_hp;

      // Si el Pokémon rival cambió, mostrar animación especial
      if (opponentPokemonChanged) {
        // Primero animar HP a 0
        animateHPChange('enemy', 0, enemyMaxHP);
        // Después de un delay, actualizar con el nuevo Pokémon
        setTimeout(() => {
          const newEnemyHP = response.battle_state.opponent_pokemon.current_hp;
          const newEnemyMaxHP = response.battle_state.opponent_pokemon.max_hp || response.battle_state.opponent_pokemon.hp;
          
          // Actualizar sprite del nuevo Pokémon
          if (response.battle_state.opponent_pokemon?.sprite_front) {
            setCurrentEnemySprite(response.battle_state.opponent_pokemon.sprite_front);
          }
          
          // Actualizar HP máximo
          setEnemyMaxHP(newEnemyMaxHP);
          enemyHPRef.current = 0; // Resetear referencia para animación
          
          // Animación de entrada del nuevo Pokémon
          setTimeout(() => {
            animateHPChange('enemy', newEnemyHP, newEnemyMaxHP);
          }, 500);
        }, 1000);
      } else {
        animateHPChange('enemy', enemyHPData, enemyMaxHP);
      }
      
      animateHPChange('player', playerHPData, playerMaxHP);
    }

    // Actualizar datos del combate según el tipo
    if (battleType === 'wild') {
      updateBattleData({
        ...battleData,
        player_pokemon: response.battle_state?.player_pokemon || battleData.player_pokemon,
        wild_pokemon: response.battle_state?.wild_pokemon || battleData.wild_pokemon
      });
    } else {
      updateBattleData({
        ...battleData,
        player_pokemon: response.battle_state?.player_pokemon || battleData.player_pokemon,
        opponent_pokemon: response.battle_state?.opponent_pokemon || battleData.opponent_pokemon
      });
      
      // Si cambió el Pokémon, actualizar sprite inmediatamente
      if (opponentPokemonChanged && response.battle_state?.opponent_pokemon?.sprite_front) {
        setCurrentEnemySprite(response.battle_state.opponent_pokemon.sprite_front);
      }
    }

    setTimeout(() => {
      addToBattleLog(response.message);
      
      // Si el entrenador sacó un nuevo Pokémon
      if (opponentPokemonChanged && response.next_pokemon_message) {
        setTimeout(() => {
          addToBattleLog(response.next_pokemon_message);
        }, 1500);
      }
    }, 800);

    if (response.effectiveness) {
      setTimeout(() => {
        setShowEffectiveness(response.effectiveness);
        setTimeout(() => setShowEffectiveness(''), 2000);
      }, 1000);
    }

    // Contraataque del enemigo
    if (response.enemy_attack_message) {
      setTimeout(() => {
        addToBattleLog(response.enemy_attack_message);

        setEnemyAttacking(true);
        setTimeout(() => {
          setEnemyAttacking(false);
          setPlayerShaking(true);
          setTimeout(() => setPlayerShaking(false), 500);
        }, 300);
      }, opponentPokemonChanged ? 3000 : 1800); // Delay más largo si cambió Pokémon
    }

    // Verificar si el combate terminó
    if (response.battle_ended) {
      setTimeout(() => {
        setBattleEnded(true);

        if (response.won) {
          const enemyName = battleType === 'wild'
            ? response.wild_pokemon_name
            : response.opponent_pokemon_name || 'el Pokémon rival';

          addToBattleLog(`¡${enemyName} fue derrotado!`);

          if (battleType === 'wild') {
            addToBattleLog(`${response.player_pokemon_name} gana ${response.experience_gained} puntos de experiencia.`);
          } else {
            // En combate trainer, también dar recompensa de dinero
            if (trainerData?.money_reward) {
              addToBattleLog(`¡Ganaste $${trainerData.money_reward}!`);
            }
          }

          setTimeout(async () => {
            try {
              const updatedTeam = await getTeamOrder();
              setPlayerTeam(updatedTeam.team);

              if (response.level_up) {
                addToBattleLog(`¡${response.player_pokemon_name} subió al nivel ${response.new_level}!`);
                const updatedCurrentPokemon = findCurrentPlayerPokemon(updatedTeam.team, battleData);
                if (updatedCurrentPokemon) {
                  setCurrentPlayerPokemon(prev => ({
                    ...prev,
                    level: response.new_level
                  }));
                }
              }
            } catch (err) {
              console.error('Error actualizando equipo:', err);
            }
          }, 500);
        } else {
          // CORRECCIÓN 2: Cuando el jugador pierde, asegurar que HP llegue a 0
          addToBattleLog('¡Has perdido el combate!');
          
          // Animación especial de derrota - HP llega a 0
          setTimeout(() => {
            animateHPChange('player', 0, playerMaxHP);
            
            // Efecto visual de derrota
            setPlayerShaking(true);
            setTimeout(() => {
              setPlayerShaking(false);
              // Cambiar sprite a debilitado (opcional)
              // Podrías cambiar a un sprite gris o con efecto
            }, 1000);
          }, 1000);
        }

        setTimeout(() => navigate('/game'), 4000);
      }, 2500);
    } else {
      setTimeout(() => {
        setActionInProgress(false);
      }, response.enemy_attack_message ? (opponentPokemonChanged ? 3500 : 2500) : 1500);
    }

  } catch (err) {
    setError('Error al atacar: ' + err.message);
    setActionInProgress(false);
  }
};

  // Función para usar item (SOLO en combate salvaje)
  // Función para usar item (con restricciones específicas)
  const handleUseItem = async (itemType) => {
    if (actionInProgress || !battleData) return;

    setActionInProgress(true);
    setShowBagMenu(false);

    try {
      const itemName = getItemName(itemType);
      addToBattleLog(`Usaste ${itemName}!`);

      // En combate trainer, bloquear solo pokeballs
      if (battleType === 'trainer' && (itemType === 'pokeball' || itemType === 'ultra_ball')) {
        addToBattleLog('¡No puedes capturar Pokémon de otros entrenadores!');
        setActionInProgress(false);
        return;
      }

      const response = await battleUseItem(battleData.battle_id, itemType);

      // VERIFICAR SI SE CAPTURÓ EL POKÉMON (solo en combate salvaje)
      if ((itemType === 'pokeball' || itemType === 'ultra_ball') && response.captured) {
        // Mostrar notificación de captura exitosa
        setCaptureNotification({
          success: true,
          pokemonName: response.wild_pokemon_name || battleData.wild_pokemon?.name || 'Pokémon salvaje',
          message: response.message || '¡Pokémon capturado!'
        });

        // Después de 3 segundos, redirigir al GameScreen
        setTimeout(() => {
          navigate('/game');
        }, 3000);

        return; // Terminar aquí para no continuar con el combate
      }

      // Si es una poción, animar HP (funciona en ambos tipos de combate)
      if (itemType.includes('potion') && response.battle_state) {
        animateHPChange('player', response.battle_state.player_pokemon.current_hp, playerMaxHP);
      }

      // Actualizar datos del combate según el tipo
      if (response.battle_state) {
        if (battleType === 'wild') {
          updateBattleData({
            ...battleData,
            player_pokemon: response.battle_state.player_pokemon,
            wild_pokemon: response.battle_state.wild_pokemon
          });
        } else {
          updateBattleData({
            ...battleData,
            player_pokemon: response.battle_state.player_pokemon,
            opponent_pokemon: response.battle_state.opponent_pokemon
          });
        }
      }

      // Actualizar mochila (solo para combate salvaje)
      if (battleType === 'wild') {
        const updatedBag = await getBag();
        setBagItems(updatedBag[0]);
      }

      setTimeout(() => {
        addToBattleLog(response.message);
      }, 800);

      // Si el enemigo contraataca
      if (response.enemy_attack_message) {
        setTimeout(() => {
          addToBattleLog(response.enemy_attack_message);

          setEnemyAttacking(true);
          setTimeout(() => {
            setEnemyAttacking(false);
            setPlayerShaking(true);
            setTimeout(() => setPlayerShaking(false), 500);

            if (response.battle_state) {
              animateHPChange('player', response.battle_state.player_pokemon.current_hp, playerMaxHP);
            }
          }, 300);
        }, 1800);

        setTimeout(() => {
          setActionInProgress(false);
        }, 2500);
      } else {
        setTimeout(() => {
          setActionInProgress(false);
        }, 1500);
      }

    } catch (err) {
      setError('Error al usar item: ' + err.message);
      setActionInProgress(false);
    }
  };

  // Función para cambiar Pokémon
  const handleSwitchPokemon = async (pokemonId) => {
    if (actionInProgress || !battleData) return;

    setActionInProgress(true);
    setShowPokemonMenu(false);

    try {
      const response = await switchPokemon(battleData.battle_id, pokemonId);

      const selectedPokemon = playerTeam.find(p => p.id === pokemonId);

      if (selectedPokemon) {
        setCurrentPlayerPokemon(selectedPokemon);
        setCurrentPlayerSprite(selectedPokemon.sprite_back);

        updateBattleData({
          ...battleData,
          player_pokemon: {
            ...response.battle_state?.player_pokemon || battleData.player_pokemon,
            id: selectedPokemon.id,
            name: selectedPokemon.pokemon_name,
            level: selectedPokemon.level
          },
          wild_pokemon: response.battle_state?.wild_pokemon || battleData.wild_pokemon,
          opponent_pokemon: response.battle_state?.opponent_pokemon || battleData.opponent_pokemon
        });

        if (response.battle_state) {
          const newHP = response.battle_state.player_pokemon.current_hp;
          const newMaxHP = response.battle_state.player_pokemon.max_hp || response.battle_state.player_pokemon.hp;
          animateHPChange('player', newHP, newMaxHP);
          setPlayerMaxHP(newMaxHP);
        }
      }

      setTimeout(() => {
        addToBattleLog(response.message);
      }, 500);

      if (response.enemy_attack_message) {
        setTimeout(() => {
          addToBattleLog(response.enemy_attack_message);

          setEnemyAttacking(true);
          setTimeout(() => {
            setEnemyAttacking(false);
            setPlayerShaking(true);
            setTimeout(() => setPlayerShaking(false), 500);

            if (response.battle_state) {
              animateHPChange('player', response.battle_state.player_pokemon.current_hp, playerMaxHP);
            }
          }, 300);
        }, 1500);

        setTimeout(() => {
          setActionInProgress(false);
        }, 2500);
      } else {
        setTimeout(() => {
          setActionInProgress(false);
        }, 1500);
      }

    } catch (err) {
      setError('Error al cambiar Pokémon: ' + err.message);
      setActionInProgress(false);
    }
  };

  // Función para huir (SOLO en combate salvaje)
  const handleFlee = async () => {
    if (actionInProgress || !battleData || battleType !== 'wild') return;

    setActionInProgress(true);

    try {
      const response = await fleeBattle(battleData.battle_id);

      addToBattleLog(response.message);
      setBattleEnded(true);

      setTimeout(() => navigate('/game'), 2000);

    } catch (err) {
      setError('Error al huir: ' + err.message);
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

  // Renderizar notificación de captura
  const renderCaptureNotification = () => {
    if (!captureNotification) return null;

    return (
      <div className="capture-notification-overlay">
        <div className="capture-notification">
          <div className="capture-success">
            <div className="capture-icon">✓</div>
            <h2>¡CAPTURA EXITOSA!</h2>
            <p className="captured-pokemon">
              Has capturado a <strong>{captureNotification.pokemonName}</strong>
            </p>
            <p className="capture-message">{captureNotification.message}</p>
            <div className="capture-sparkles">
              <div className="sparkle"></div>
              <div className="sparkle"></div>
              <div className="sparkle"></div>
              <div className="sparkle"></div>
              <div className="sparkle"></div>
            </div>
            <p className="redirect-message">Redirigiendo al mapa en 3 segundos...</p>
          </div>
        </div>
      </div>
    );
  };

  // Renderizar menú de movimientos
  const renderMoveMenu = () => {
    if (!battleData || !battleData.player_pokemon?.moves) return null;

    return (
      <div className="move-menu-overlay">
        <div className="move-menu">
          <h3>Elige un movimiento</h3>
          <div className="move-grid">
            {battleData.player_pokemon.moves.map((move, index) => (
              <div key={move.id || index} className="move-option">
                <button
                  className="move-button"
                  onClick={() => handleAttack(move)}
                  disabled={actionInProgress}
                >
                  <span className="move-name">{move.name}</span>
                  <span className="move-pp">
                    PP: {move.current_pp || move.pp}/{move.max_pp || move.pp}
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

  // Renderizar menú de mochila (SOLO para combate salvaje)
  // Renderizar menú de mochila (con restricciones específicas)
  const renderBagMenu = () => {
    if (!bagItems && battleType === 'wild') return null;

    const items = [
      { type: 'pokeball', name: 'Pokéball', count: bagItems?.pokeballs || 0 },
      { type: 'ultra_ball', name: 'Ultraball', count: bagItems?.ultra_balls || 0 },
      { type: 'potion', name: 'Poción', count: bagItems?.potions || 0 },
      { type: 'super_potion', name: 'Superpoción', count: bagItems?.super_potions || 0 },
      { type: 'hyper_potion', name: 'Hiperpoción', count: bagItems?.hyper_potions || 0 }
    ];

    return (
      <div className="bag-menu-overlay">
        <div className="bag-menu">
          <h3>Mochila</h3>
          {battleType === 'trainer' && (
            <div className="trainer-bag-warning">
              <p>⚠️ No puedes capturar Pokémon de entrenadores</p>
            </div>
          )}
          <div className="item-grid">
            {items.map((item) => {
              // Determinar si el item está deshabilitado
              let isDisabled = actionInProgress;
              let reason = '';

              if (item.count === 0) {
                isDisabled = true;
                reason = 'Sin existencias';
              } else if (battleType === 'trainer' &&
                (item.type === 'pokeball' || item.type === 'ultra_ball')) {
                isDisabled = true;
                reason = 'No disponible vs entrenadores';
              }

              return (
                <div key={item.type} className="item-option">
                  <button
                    className={`item-button ${isDisabled ? 'disabled-item' : ''}`}
                    onClick={() => handleUseItem(item.type)}
                    disabled={isDisabled}
                    title={reason}
                  >
                    <span className="item-name">{item.name}</span>
                    <span className="item-count">x{item.count}</span>
                    {reason && (
                      <span className="item-disabled-reason">{reason}</span>
                    )}
                  </button>
                </div>
              );
            })}
          </div>
          <button
            className="back-button"
            onClick={() => setShowBagMenu(false)}
            disabled={actionInProgress}
          >
            Atrás
          </button>
        </div>
      </div>
    );
  };

  // Renderizar menú de Pokémon
  const renderPokemonMenu = () => {
    return (
      <div className="pokemon-menu-overlay">
        <div className="pokemon-menu">
          <h3>Cambiar Pokémon</h3>
          <div className="pokemon-grid">
            {playerTeam.map((pokemon) => (
              <div key={pokemon.id} className="pokemon-option">
                <button
                  className="pokemon-button"
                  onClick={() => handleSwitchPokemon(pokemon.id)}
                  disabled={
                    actionInProgress ||
                    pokemon.id === battleData?.player_pokemon?.id ||
                    pokemon.current_hp <= 0
                  }
                >
                  <img
                    src={pokemon.sprite_front || `https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/${pokemon.pokemon || 1}.png`}
                    alt={pokemon.pokemon_name}
                  />
                  <div className="pokemon-info">
                    <span className="pokemon-name">{pokemon.nickname || pokemon.pokemon_name}</span>
                    <span className="pokemon-level">Lv. {pokemon.level}</span>
                    <div className="pokemon-hp">
                      PS: {pokemon.current_hp}/{pokemon.hp}
                    </div>
                  </div>
                  {pokemon.current_hp <= 0 && (
                    <span className="fainted-badge">DEBILITADO</span>
                  )}
                </button>
              </div>
            ))}
          </div>
          <button
            className="back-button"
            onClick={() => setShowPokemonMenu(false)}
            disabled={actionInProgress}
          >
            Atrás
          </button>
        </div>
      </div>
    );
  };

  // Renderizar efectividad del ataque
  const renderEffectiveness = () => {
    if (!showEffectiveness) return null;

    let message = '';
    switch (showEffectiveness) {
      case 'super_effective':
        message = '¡Es muy efectivo!';
        break;
      case 'not_very_effective':
        message = 'No es muy efectivo...';
        break;
      case 'no_effect':
        message = 'No afecta al Pokémon rival';
        break;
      default:
        return null;
    }

    return <div className="effectiveness-message">{message}</div>;
  };

  // Renderizar información del entrenador
  const renderTrainerInfo = () => {
    if (battleType !== 'trainer' || !trainerData) return null;

    return (
      <div className="trainer-info">
        <div className="trainer-name">
          <span className="trainer-label">Entrenador:</span>
          <span className="trainer-value">{trainerData.name}</span>
        </div>
        <div className="trainer-reward">
          <span className="reward-label">Recompensa:</span>
          <span className="reward-value">${trainerData.money_reward || 0}</span>
        </div>
      </div>
    );
  };

  // Si el combate terminó
  if (battleEnded && !loading && !error) {
    return (
      <div className="battle-ended">
        <h2>Combate terminado</h2>
        <button onClick={() => navigate('/game')}>Volver al mapa</button>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="battle-loading">
        <div className="battle-spinner"></div>
        <p>Iniciando combate...</p>
      </div>
    );
  }

  if (error || !battleData) {
    return (
      <div className="battle-error">
        <h2>Error en el combate</h2>
        <p>{error || 'No se pudo iniciar el combate'}</p>
        <button onClick={() => navigate('/game')}>Volver al mapa</button>
      </div>
    );
  }

  return (
    <div className="battle-screen">
      {/* Notificación de captura (si existe) */}
      {renderCaptureNotification()}

      {/* Si hay notificación de captura, no mostrar el combate */}
      {!captureNotification && (
        <>
          {/* Fondo principal del combate */}
          <div className="battle-background">

            {/* Información del entrenador (solo para trainer) */}
            {renderTrainerInfo()}

            {/* Pokémon Enemigo - EN LA PARTE SUPERIOR DERECHA */}
            <div className="enemy-container">
              {/* Sprite frontal del Pokémon enemigo */}
              <div className={`enemy-sprite ${enemyShaking ? 'shaking' : ''} ${enemyAttacking ? 'attacking' : ''}`}>
                <img
                  src={currentEnemySprite ||
                    (battleType === 'wild'
                      ? battleData.wild_pokemon?.sprite_front
                      : battleData.opponent_pokemon?.sprite_front) ||
                    'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/1.png'}
                  alt={battleType === 'wild'
                    ? battleData.wild_pokemon?.name
                    : battleData.opponent_pokemon?.pokemon_name || 'Pokémon rival'}
                  onError={(e) => {
                    e.target.onerror = null;
                    e.target.src = 'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/1.png';
                  }}
                />
              </div>

              {/* Información del enemigo */}
              <div className="enemy-info-panel">
                <div className="enemy-name">
                  {battleType === 'wild'
                    ? battleData.wild_pokemon?.name
                    : battleData.opponent_pokemon?.pokemon_name || 'Pokémon rival'}
                  <span className="enemy-level">
                    Lv.{battleType === 'wild'
                      ? battleData.wild_pokemon?.level
                      : battleData.opponent_pokemon?.level || 1}
                  </span>
                </div>
                {renderHPBar(enemyHP, enemyMaxHP, true)}
              </div>
            </div>

            {/* Pokémon del Jugador - EN LA PARTE INFERIOR IZQUIERDA */}
            <div className="player-container">
              {/* Sprite de espalda del Pokémon jugador */}
              <div className={`player-sprite ${playerShaking ? 'shaking' : ''} ${playerAttacking ? 'attacking' : ''}`}>
                <img
                  src={currentPlayerSprite || currentPlayerPokemon?.sprite_back || 'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/back/1.png'}
                  alt={currentPlayerPokemon?.pokemon_name || 'Tu Pokémon'}
                  onError={(e) => {
                    e.target.onerror = null;
                    e.target.src = 'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/back/1.png';
                  }}
                />
              </div>

              {/* Información del jugador */}
              <div className="player-info-panel">
                <div className="player-name">
                  {currentPlayerPokemon?.pokemon_name || battleData.player_pokemon?.name || 'Tu Pokémon'}
                  <span className="player-level">Lv.{currentPlayerPokemon?.level || battleData.player_pokemon?.level || 1}</span>
                </div>
                {renderHPBar(playerHP, playerMaxHP, false)}
              </div>
            </div>

            {/* Logs del combate - EN LA PARTE INFERIOR */}
            <div className="battle-log-panel">
              <div className="battle-logs">
                {battleLog.map((message, index) => (
                  <p key={index}>{message}</p>
                ))}
              </div>
            </div>

            {/* Menú de acciones - AL LADO DE LOS LOGS */}
            <div className="action-panel">
              <div className="action-buttons">
                <div className="action-row">
                  <button
                    className="action-button fight"
                    onClick={() => setShowMoveMenu(true)}
                    disabled={actionInProgress}
                  >
                    LUCHAR
                  </button>
                  <button
                    className="action-button bag"
                    onClick={() => setShowBagMenu(true)}
                    disabled={actionInProgress}
                  // REMOVED: || battleType !== 'wild' 
                  >
                    MOCHILA
                  </button>
                </div>
                <div className="action-row">
                  <button
                    className="action-button pokemon"
                    onClick={() => setShowPokemonMenu(true)}
                    disabled={actionInProgress}
                  >
                    POKÉMON
                  </button>
                  <button
                    className="action-button run"
                    onClick={handleFlee}
                    disabled={actionInProgress || battleType !== 'wild'}
                  >
                    HUIR
                  </button>
                </div>
              </div>
            </div>

            {showEffectiveness && renderEffectiveness()}
            {damageEffect && (
              <div className={`damage-effect ${damageEffect}`}></div>
            )}

          </div>

          {showMoveMenu && renderMoveMenu()}
          {showBagMenu && renderBagMenu()}
          {showPokemonMenu && renderPokemonMenu()}

          <button
            className="back-to-map"
            onClick={() => navigate('/game')}
          >
            Volver al mapa
          </button>
        </>
      )}
    </div>
  );
};

export default BattleScreen;