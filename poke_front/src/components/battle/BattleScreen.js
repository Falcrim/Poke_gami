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

  const [enemyShaking, setEnemyShaking] = useState(false);
  const [playerShaking, setPlayerShaking] = useState(false);
  const [playerAttacking, setPlayerAttacking] = useState(false);
  const [enemyAttacking, setEnemyAttacking] = useState(false);
  const [damageEffect, setDamageEffect] = useState(null);
  const [showEffectiveness, setShowEffectiveness] = useState('');

  const [enemyHP, setEnemyHP] = useState(0);
  const [playerHP, setPlayerHP] = useState(0);
  const [enemyMaxHP, setEnemyMaxHP] = useState(0);
  const [playerMaxHP, setPlayerMaxHP] = useState(0);

  const [currentEnemySprite, setCurrentEnemySprite] = useState('');
  const [currentPlayerSprite, setCurrentPlayerSprite] = useState('');

  const [currentPlayerPokemon, setCurrentPlayerPokemon] = useState(null);

  const [trainerData, setTrainerData] = useState(null);

  const enemyHPRef = useRef(0);
  const playerHPRef = useRef(0);

  const [captureNotification, setCaptureNotification] = useState(null);

  const [playerSwitching, setPlayerSwitching] = useState(false);
  const [enemySwitching, setEnemySwitching] = useState(false);
  const [playerSpriteScale, setPlayerSpriteScale] = useState(1);
  const [enemySpriteScale, setEnemySpriteScale] = useState(1);
  const [isPlayerFainted, setIsPlayerFainted] = useState(false);
  const [isEnemyFainted, setIsEnemyFainted] = useState(false);

  const [originalWildPokemon, setOriginalWildPokemon] = useState(null);
  const [originalOpponentPokemon, setOriginalOpponentPokemon] = useState(null);

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

  const findCurrentPlayerPokemon = (team, battleData) => {
    if (!team || !battleData?.player_pokemon) return null;
    return team.find(p => p.id === battleData.player_pokemon.id) || team[0];
  };

  const updateSprites = () => {
    if (!battleData) return;
    
    if (battleType === 'wild' && battleData.wild_pokemon) {
      const enemySprite = originalWildPokemon?.sprite_front || 
                         battleData.wild_pokemon.sprite_front || 
                         `https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/${battleData.wild_pokemon.pokemon || 1}.png`;
      
      setCurrentEnemySprite(enemySprite);
    } else if (battleType === 'trainer' && battleData.opponent_pokemon) {
      const enemySprite = originalOpponentPokemon?.sprite_front || 
                         battleData.opponent_pokemon.sprite_front || 
                         `https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/${battleData.opponent_pokemon.pokemon || 1}.png`;
      
      setCurrentEnemySprite(enemySprite);
    }
    
    if (currentPlayerPokemon) {
      setCurrentPlayerSprite(currentPlayerPokemon.sprite_back || 
        `https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/back/${currentPlayerPokemon.pokemon || 1}.png`);
    } else if (battleData.player_pokemon) {
      const currentPokemon = findCurrentPlayerPokemon(playerTeam, battleData);
      if (currentPokemon) {
        setCurrentPlayerPokemon(currentPokemon);
        setCurrentPlayerSprite(currentPokemon.sprite_back || 
          `https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/back/${currentPokemon.pokemon || 1}.png`);
      }
    }
  };

  const playSwitchAnimation = async (target, newSprite, callback) => {
    if (target === 'player') {
      setPlayerSwitching(true);
      
      for (let scale = 1; scale >= 0; scale -= 0.1) {
        await new Promise(resolve => setTimeout(resolve, 30));
        setPlayerSpriteScale(scale);
      }
      
      setCurrentPlayerSprite(newSprite);
      
      for (let scale = 0; scale <= 1; scale += 0.1) {
        await new Promise(resolve => setTimeout(resolve, 30));
        setPlayerSpriteScale(scale);
      }
      
      setPlayerSwitching(false);
    } else if (target === 'enemy') {
      setEnemySwitching(true);
      
      for (let scale = 1; scale >= 0; scale -= 0.1) {
        await new Promise(resolve => setTimeout(resolve, 30));
        setEnemySpriteScale(scale);
      }
      
      setCurrentEnemySprite(newSprite);
      
      for (let scale = 0; scale <= 1; scale += 0.1) {
        await new Promise(resolve => setTimeout(resolve, 30));
        setEnemySpriteScale(scale);
      }
      
      setEnemySwitching(false);
    }
    
    if (callback) callback();
  };

  useEffect(() => {
    const initBattle = async () => {
      try {
        setLoading(true);
        setError('');
        setBattleEnded(false);
        setCaptureNotification(null);
        setTrainerData(null);
        
        setPlayerSwitching(false);
        setEnemySwitching(false);
        setPlayerSpriteScale(1);
        setEnemySpriteScale(1);
        setIsPlayerFainted(false);
        setIsEnemyFainted(false);
        
        setCurrentEnemySprite('');
        setCurrentPlayerSprite('');
        
        setOriginalWildPokemon(null);
        setOriginalOpponentPokemon(null);

        const teamData = await getTeamOrder();
        setPlayerTeam(teamData.team);

        const bagData = await getBag();
        setBagItems(bagData[0] || {});

        if (battleType === 'wild') {
          const battleResponse = await startWildBattle();
          
          setOriginalWildPokemon({
            ...battleResponse.wild_pokemon,
            sprite_front: battleResponse.wild_pokemon.sprite_front || 
              `https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/${battleResponse.wild_pokemon.pokemon || 1}.png`,
            sprite_back: battleResponse.wild_pokemon.sprite_back || 
              `https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/back/${battleResponse.wild_pokemon.pokemon || 1}.png`
          });
          
          setBattleData(battleResponse);

          const currentPokemon = findCurrentPlayerPokemon(teamData.team, battleResponse);
          setCurrentPlayerPokemon(currentPokemon);

          updateSprites();

          setEnemyHP(battleResponse.wild_pokemon.current_hp);
          setPlayerHP(battleResponse.player_pokemon.current_hp);
          setEnemyMaxHP(battleResponse.wild_pokemon.max_hp || battleResponse.wild_pokemon.hp);
          setPlayerMaxHP(battleResponse.player_pokemon.max_hp || battleResponse.player_pokemon.hp);

          enemyHPRef.current = battleResponse.wild_pokemon.current_hp;
          playerHPRef.current = battleResponse.player_pokemon.current_hp;

          setBattleLog([battleResponse.message]);

        } else if (battleType === 'trainer') {
          const battleResponse = await startTrainerBattle();
          
          setOriginalOpponentPokemon({
            ...battleResponse.opponent_pokemon,
            sprite_front: battleResponse.opponent_pokemon.sprite_front || 
              `https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/${battleResponse.opponent_pokemon.pokemon || 1}.png`,
            sprite_back: battleResponse.opponent_pokemon.sprite_back || 
              `https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/back/${battleResponse.opponent_pokemon.pokemon || 1}.png`
          });
          
          setBattleData(battleResponse);
          setTrainerData(battleResponse.trainer);

          const currentPokemon = findCurrentPlayerPokemon(teamData.team, battleResponse);
          setCurrentPlayerPokemon(currentPokemon);

          updateSprites();

          setEnemyHP(battleResponse.opponent_pokemon.current_hp);
          setPlayerHP(battleResponse.player_pokemon.current_hp);
          setEnemyMaxHP(battleResponse.opponent_pokemon.max_hp || battleResponse.opponent_pokemon.hp);
          setPlayerMaxHP(battleResponse.player_pokemon.max_hp || battleResponse.player_pokemon.hp);

          enemyHPRef.current = battleResponse.opponent_pokemon.current_hp;
          playerHPRef.current = battleResponse.player_pokemon.current_hp;

          setBattleLog([battleResponse.message]);
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

  useEffect(() => {
    updateSprites();
  }, [battleData, currentPlayerPokemon]);

  const addToBattleLog = (message) => {
    setBattleLog(prev => {
      const newLog = [...prev, message];
      return newLog.slice(-2);
    });
  };

  const animateHPChange = (target, newHP, maxHP, onComplete = null) => {
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
            
            if (i === steps) {
              if (newValue <= 0 && target === 'enemy') {
                setIsEnemyFainted(true);
              }
              if (onComplete) onComplete();
              resolve();
            }
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
            
            if (i === steps) {
              if (newValue <= 0 && target === 'player') {
                setIsPlayerFainted(true);
              }
              if (onComplete) onComplete();
              resolve();
            }
          }, i * delay);
        }
      }
    });
  };

  const updateBattleData = (newBattleData) => {
    const updatedData = { ...newBattleData };
    
    if (battleType === 'wild' && updatedData.wild_pokemon && originalWildPokemon) {
      updatedData.wild_pokemon = {
        ...updatedData.wild_pokemon,
        sprite_front: originalWildPokemon.sprite_front,
        sprite_back: originalWildPokemon.sprite_back,
        name: updatedData.wild_pokemon.name || originalWildPokemon.name,
        level: updatedData.wild_pokemon.level || originalWildPokemon.level,
        pokemon: updatedData.wild_pokemon.pokemon || originalWildPokemon.pokemon
      };
    }
    
    if (battleType === 'trainer' && updatedData.opponent_pokemon && originalOpponentPokemon) {
      updatedData.opponent_pokemon = {
        ...updatedData.opponent_pokemon,
        sprite_front: originalOpponentPokemon.sprite_front,
        sprite_back: originalOpponentPokemon.sprite_back,
        pokemon_name: updatedData.opponent_pokemon.pokemon_name || originalOpponentPokemon.pokemon_name,
        level: updatedData.opponent_pokemon.level || originalOpponentPokemon.level,
        pokemon: updatedData.opponent_pokemon.pokemon || originalOpponentPokemon.pokemon
      };
    }
    
    if (updatedData.player_pokemon && currentPlayerPokemon) {
      updatedData.player_pokemon = {
        ...updatedData.player_pokemon,
        sprite_back: updatedData.player_pokemon.sprite_back || currentPlayerPokemon.sprite_back
      };
    }

    setBattleData(updatedData);

    if (updatedData?.player_pokemon) {
      const newCurrentPokemon = findCurrentPlayerPokemon(playerTeam, updatedData);
      if (newCurrentPokemon && newCurrentPokemon.id !== currentPlayerPokemon?.id) {
        setCurrentPlayerPokemon(newCurrentPokemon);
      }
    }
    
    updateSprites();
  };

  const handleAttack = async (move) => {
    if (actionInProgress || !battleData || !move) return;

    setActionInProgress(true);
    setShowMoveMenu(false);

    try {
      const enemyName = battleType === 'wild'
        ? battleData.wild_pokemon?.name
        : battleData.opponent_pokemon?.pokemon_name;

      addToBattleLog(`${battleData.player_pokemon.name} usó ${move.name}!`);

      setPlayerAttacking(true);
      setTimeout(() => setPlayerAttacking(false), 300);

      setDamageEffect('player-attack');
      setTimeout(() => {
        setDamageEffect(null);
        setEnemyShaking(true);
        setTimeout(() => setEnemyShaking(false), 500);
      }, 200);

      const response = await attackPokemon(battleData.battle_id, move.id);

      const enemyFainted = battleType === 'wild'
        ? response.battle_state?.wild_pokemon?.current_hp <= 0
        : response.battle_state?.opponent_pokemon?.current_hp <= 0;

      if (response.battle_state) {
        const enemyHPData = battleType === 'wild'
          ? response.battle_state.wild_pokemon.current_hp
          : response.battle_state.opponent_pokemon.current_hp;

        const playerHPData = response.battle_state.player_pokemon.current_hp;

        await animateHPChange('enemy', enemyHPData, enemyMaxHP);
        
        if (enemyFainted) {
          setIsEnemyFainted(true);
          
          if (battleType === 'trainer' && response.next_pokemon) {
            setOriginalOpponentPokemon({
              ...response.next_pokemon,
              sprite_front: response.next_pokemon.sprite_front || 
                `https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/${response.next_pokemon.pokemon || 1}.png`
            });
            
            setTimeout(() => {
              addToBattleLog(`¡${enemyName} fue derrotado!`);
            }, 800);
            
            setTimeout(() => {
              addToBattleLog(`${trainerData.name} envía a ${response.next_pokemon.pokemon_name}!`);
              
              playSwitchAnimation('enemy', response.next_pokemon.sprite_front, () => {
                const updatedData = {
                  ...battleData,
                  opponent_pokemon: response.next_pokemon
                };
                updateBattleData(updatedData);
                
                setIsEnemyFainted(false);
                
                const newEnemyHP = response.next_pokemon.current_hp;
                const newEnemyMaxHP = response.next_pokemon.max_hp || response.next_pokemon.hp;
                setEnemyMaxHP(newEnemyMaxHP);
                enemyHPRef.current = 0;
                
                setTimeout(() => {
                  animateHPChange('enemy', newEnemyHP, newEnemyMaxHP);
                }, 500);
              });
            }, 2000);
          }
        }
        
        animateHPChange('player', playerHPData, playerMaxHP);
      }

      const updatedData = {
        ...battleData,
        player_pokemon: {
          ...(response.battle_state?.player_pokemon || battleData.player_pokemon),
          sprite_back: currentPlayerPokemon?.sprite_back || battleData.player_pokemon.sprite_back
        }
      };

      if (battleType === 'wild') {
        updatedData.wild_pokemon = {
          ...(response.battle_state?.wild_pokemon || battleData.wild_pokemon),
          sprite_front: originalWildPokemon?.sprite_front || battleData.wild_pokemon.sprite_front,
          name: originalWildPokemon?.name || battleData.wild_pokemon.name,
          level: originalWildPokemon?.level || battleData.wild_pokemon.level,
          pokemon: originalWildPokemon?.pokemon || battleData.wild_pokemon.pokemon
        };
      } else {
        updatedData.opponent_pokemon = {
          ...(response.battle_state?.opponent_pokemon || battleData.opponent_pokemon),
          sprite_front: originalOpponentPokemon?.sprite_front || battleData.opponent_pokemon.sprite_front,
          pokemon_name: originalOpponentPokemon?.pokemon_name || battleData.opponent_pokemon.pokemon_name,
          level: originalOpponentPokemon?.level || battleData.opponent_pokemon.level,
          pokemon: originalOpponentPokemon?.pokemon || battleData.opponent_pokemon.pokemon
        };
      }

      updateBattleData(updatedData);

      setTimeout(() => {
        addToBattleLog(response.message);
      }, 800);

      if (response.effectiveness) {
        setTimeout(() => {
          setShowEffectiveness(response.effectiveness);
          setTimeout(() => setShowEffectiveness(''), 2000);
        }, 1000);
      }

      if (response.enemy_attack_message && !enemyFainted) {
        setTimeout(() => {
          addToBattleLog(response.enemy_attack_message);

          setEnemyAttacking(true);
          setTimeout(() => {
            setEnemyAttacking(false);
            setPlayerShaking(true);
            setTimeout(() => setPlayerShaking(false), 500);
          }, 300);
        }, enemyFainted ? 2500 : 1800);
      }

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
            addToBattleLog('¡Has perdido el combate!');
            
            setTimeout(() => {
              animateHPChange('player', 0, playerMaxHP, () => {
                setIsPlayerFainted(true);
                setPlayerShaking(true);
                setTimeout(() => setPlayerShaking(false), 1000);
              });
            }, 1000);
          }

          setTimeout(() => navigate('/game'), 4000);
        }, 2500);
      } else {
        setTimeout(() => {
          setActionInProgress(false);
        }, enemyFainted ? 3500 : 2500);
      }

    } catch (err) {
      setError('Error al atacar: ' + err.message);
      setActionInProgress(false);
    }
  };

  const handleUseItem = async (itemType) => {
    if (actionInProgress || !battleData) return;

    setActionInProgress(true);
    setShowBagMenu(false);

    try {
      const itemName = getItemName(itemType);
      addToBattleLog(`Usaste ${itemName}!`);

      if (battleType === 'trainer' && (itemType === 'pokeball' || itemType === 'ultra_ball')) {
        addToBattleLog('¡No puedes capturar Pokémon de otros entrenadores!');
        setActionInProgress(false);
        return;
      }

      const response = await battleUseItem(battleData.battle_id, itemType);

      if ((itemType === 'pokeball' || itemType === 'ultra_ball') && response.captured) {
        setCaptureNotification({
          success: true,
          pokemonName: response.wild_pokemon_name || battleData.wild_pokemon?.name || 'Pokémon salvaje',
          message: response.message || '¡Pokémon capturado!'
        });

        setTimeout(() => {
          navigate('/game');
        }, 3000);

        return;
      }

      if (itemType.includes('potion') && response.battle_state) {
        animateHPChange('player', response.battle_state.player_pokemon.current_hp, playerMaxHP);
      }

      const updatedData = {
        ...battleData,
        player_pokemon: {
          ...(response.battle_state?.player_pokemon || battleData.player_pokemon),
          sprite_back: currentPlayerPokemon?.sprite_back || battleData.player_pokemon.sprite_back
        }
      };

      if (battleType === 'wild') {
        updatedData.wild_pokemon = {
          ...(response.battle_state?.wild_pokemon || battleData.wild_pokemon),
          sprite_front: originalWildPokemon?.sprite_front || battleData.wild_pokemon.sprite_front,
          name: originalWildPokemon?.name || battleData.wild_pokemon.name,
          level: originalWildPokemon?.level || battleData.wild_pokemon.level,
          pokemon: originalWildPokemon?.pokemon || battleData.wild_pokemon.pokemon
        };
      } else {
        updatedData.opponent_pokemon = {
          ...(response.battle_state?.opponent_pokemon || battleData.opponent_pokemon),
          sprite_front: originalOpponentPokemon?.sprite_front || battleData.opponent_pokemon.sprite_front,
          pokemon_name: originalOpponentPokemon?.pokemon_name || battleData.opponent_pokemon.pokemon_name,
          level: originalOpponentPokemon?.level || battleData.opponent_pokemon.level,
          pokemon: originalOpponentPokemon?.pokemon || battleData.opponent_pokemon.pokemon
        };
      }

      updateBattleData(updatedData);

      const updatedBag = await getBag();
      setBagItems(updatedBag[0] || {});

      setTimeout(() => {
        addToBattleLog(response.message);
      }, 800);

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

  const handleSwitchPokemon = async (pokemonId) => {
    if (actionInProgress || !battleData) return;

    setActionInProgress(true);
    setShowPokemonMenu(false);

    try {
      const response = await switchPokemon(battleData.battle_id, pokemonId);

      const selectedPokemon = playerTeam.find(p => p.id === pokemonId);

      if (selectedPokemon) {
        await playSwitchAnimation('player', selectedPokemon.sprite_back, () => {
          setCurrentPlayerPokemon(selectedPokemon);
          
          const updatedData = {
            ...battleData,
            player_pokemon: {
              ...(response.battle_state?.player_pokemon || battleData.player_pokemon),
              id: selectedPokemon.id,
              name: selectedPokemon.pokemon_name,
              level: selectedPokemon.level,
              sprite_back: selectedPokemon.sprite_back
            }
          };

          if (battleType === 'wild') {
            updatedData.wild_pokemon = {
              ...(response.battle_state?.wild_pokemon || battleData.wild_pokemon),
              sprite_front: originalWildPokemon?.sprite_front || battleData.wild_pokemon.sprite_front,
              name: originalWildPokemon?.name || battleData.wild_pokemon.name,
              level: originalWildPokemon?.level || battleData.wild_pokemon.level,
              pokemon: originalWildPokemon?.pokemon || battleData.wild_pokemon.pokemon
            };
          } else {
            updatedData.opponent_pokemon = {
              ...(response.battle_state?.opponent_pokemon || battleData.opponent_pokemon),
              sprite_front: originalOpponentPokemon?.sprite_front || battleData.opponent_pokemon.sprite_front,
              pokemon_name: originalOpponentPokemon?.pokemon_name || battleData.opponent_pokemon.pokemon_name,
              level: originalOpponentPokemon?.level || battleData.opponent_pokemon.level,
              pokemon: originalOpponentPokemon?.pokemon || battleData.opponent_pokemon.pokemon
            };
          }

          updateBattleData(updatedData);

          if (response.battle_state) {
            const newHP = response.battle_state.player_pokemon.current_hp;
            const newMaxHP = response.battle_state.player_pokemon.max_hp || response.battle_state.player_pokemon.hp;
            animateHPChange('player', newHP, newMaxHP);
            setPlayerMaxHP(newMaxHP);
          }
        });
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

  const getEnemyData = () => {
    if (!battleData) return { name: '', level: 1, hp: 0, pokemon: 1 };
    
    if (battleType === 'wild') {
      const wildData = originalWildPokemon || battleData.wild_pokemon;
      return {
        name: wildData?.name || 'Pokémon salvaje',
        level: wildData?.level || 1,
        pokemon: wildData?.pokemon || 1,
        current_hp: enemyHP,
        max_hp: enemyMaxHP
      };
    } else {
      const opponentData = originalOpponentPokemon || battleData.opponent_pokemon;
      return {
        name: opponentData?.pokemon_name || 'Pokémon rival',
        level: opponentData?.level || 1,
        pokemon: opponentData?.pokemon || 1,
        current_hp: enemyHP,
        max_hp: enemyMaxHP
      };
    }
  };

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

  const renderBagMenu = () => {
    if (!bagItems) return null;

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

  const enemyData = getEnemyData();

  return (
    <div className="battle-screen">
      {renderCaptureNotification()}

      {!captureNotification && (
        <>
          <div className="battle-background">

            {renderTrainerInfo()}

            <div className="enemy-container">
              <div className={`enemy-sprite ${enemyShaking ? 'shaking' : ''} ${enemyAttacking ? 'attacking' : ''} ${enemySwitching ? 'switching' : ''} ${isEnemyFainted ? 'fainted' : ''}`}
                   style={{ transform: `scale(${enemySpriteScale})` }}>
                <img
                  src={currentEnemySprite || 
                    `https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/${enemyData.pokemon || 1}.png`}
                  alt={enemyData.name}
                  onError={(e) => {
                    e.target.onerror = null;
                    e.target.src = `https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/${enemyData.pokemon || 1}.png`;
                  }}
                />
              </div>

              <div className="enemy-info-panel">
                <div className="enemy-name">
                  {enemyData.name}
                  <span className="enemy-level">
                    Lv.{enemyData.level}
                  </span>
                </div>
                {renderHPBar(enemyHP, enemyMaxHP, true)}
              </div>
            </div>

            <div className="player-container">

              <div className={`player-sprite ${playerShaking ? 'shaking' : ''} ${playerAttacking ? 'attacking' : ''} ${playerSwitching ? 'switching' : ''} ${isPlayerFainted ? 'fainted' : ''}`}
                   style={{ transform: `scale(${playerSpriteScale})` }}>
                <img
                  src={currentPlayerSprite || 
                    currentPlayerPokemon?.sprite_back || 
                    `https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/back/${currentPlayerPokemon?.pokemon || 1}.png`}
                  alt={currentPlayerPokemon?.pokemon_name || 'Tu Pokémon'}
                  onError={(e) => {
                    e.target.onerror = null;
                    e.target.src = 'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/back/1.png';
                  }}
                />
              </div>

              <div className="player-info-panel">
                <div className="player-name">
                  {currentPlayerPokemon?.pokemon_name || battleData.player_pokemon?.name || 'Tu Pokémon'}
                  <span className="player-level">Lv.{currentPlayerPokemon?.level || battleData.player_pokemon?.level || 1}</span>
                </div>
                {renderHPBar(playerHP, playerMaxHP, false)}
              </div>
            </div>

            <div className="battle-log-panel">
              <div className="battle-logs">
                {battleLog.map((message, index) => (
                  <p key={index}>{message}</p>
                ))}
              </div>
            </div>

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