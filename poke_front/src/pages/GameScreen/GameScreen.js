import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  getLocations,
  travelToLocation,
  getCurrentPlayer,
  getPokedex,
  healTeam,
  getShopItems,
  buyItem,
  getTeamAndReserve,
  moveToReserve,
  moveToTeam,
  getTeamOrder,
  movePokemonToPosition,
  getCurrentUser,
  getBag,
  teachMove,
  forgetMove
} from '../../services/gameService';
import './GameScreen.css';

const GameScreen = () => {
  const [locations, setLocations] = useState([]);
  const [currentLocation, setCurrentLocation] = useState(null);
  const [connectedLocations, setConnectedLocations] = useState([]);
  const [pokedex, setPokedex] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [traveling, setTraveling] = useState(false);
  const [userMoney, setUserMoney] = useState(0);
  const [bag, setBag] = useState(null);
  const navigate = useNavigate();

  const [activeCityTab, setActiveCityTab] = useState('pokemon-center');
  const [activeTeamTab, setActiveTeamTab] = useState('team');
  const [shopItems, setShopItems] = useState([]);
  const [shopLoading, setShopLoading] = useState(false);

  const [teamData, setTeamData] = useState({ team: [], team_count: 0, max_team_size: 6 });
  const [teamReserveData, setTeamReserveData] = useState({ team: [], reserve: [], team_count: 0, reserve_count: 0, max_team_size: 6 });

  const [teamLoading, setTeamLoading] = useState(false);
  const [healing, setHealing] = useState(false);
  const [buying, setBuying] = useState(null);
  const [healingAnimation, setHealingAnimation] = useState(false);

  const [dragOverIndex, setDragOverIndex] = useState(null);

  const [selectedPokemon, setSelectedPokemon] = useState(null);
  const [pokemonDetailTab, setPokemonDetailTab] = useState('stats');
  const [teachingMove, setTeachingMove] = useState(false);
  const [forgettingMove, setForgettingMove] = useState(false);

  useEffect(() => {
    const fetchGameData = async () => {
      try {
        setLoading(true);
        const [locationsData, playerData, pokedexData, userData, bagData] = await Promise.all([
          getLocations(),
          getCurrentPlayer(),
          getPokedex(),
          getCurrentUser(),
          getBag()
        ]);

        setLocations(locationsData);
        setPokedex(pokedexData);
        setUserMoney(userData.player_info?.money || 0);
        setBag(bagData[0]);

        const currentPlayer = playerData[0];
        if (currentPlayer) {
          const currentLoc = locationsData.find(loc => loc.id === currentPlayer.current_location);
          setCurrentLocation(currentLoc);
          setConnectedLocations(currentPlayer.connected_locations || []);
        }

      } catch (err) {
        setError('Error al cargar el mapa: ' + (err.message || 'Error desconocido'));
        console.error('Error fetching game data:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchGameData();
  }, []);

  useEffect(() => {
    if (currentLocation?.location_type === 'town') {
      fetchShopItems();
      fetchTeamData();
      fetchTeamAndReserveData();
    }
  }, [currentLocation]);

  const fetchShopItems = async () => {
    try {
      setShopLoading(true);
      const items = await getShopItems();
      setShopItems(items);
    } catch (err) {
      setError('Error al cargar la tienda');
      console.error('Error fetching shop:', err);
    } finally {
      setShopLoading(false);
    }
  };

  const fetchTeamData = async () => {
    try {
      setTeamLoading(true);
      const data = await getTeamOrder();
      console.log('Team data from getTeamOrder:', data);
      setTeamData(data);
    } catch (err) {
      console.error('Error fetching team:', err);
    } finally {
      setTeamLoading(false);
    }
  };

  const fetchTeamAndReserveData = async () => {
    try {
      const data = await getTeamAndReserve();
      console.log('Team and reserve data:', data);
      setTeamReserveData(data);
    } catch (err) {
      console.error('Error fetching team and reserve:', err);
    }
  };

  const handleTravel = async (locationId) => {
    if (traveling) return;

    const isConnected = connectedLocations.some(loc => loc.id === locationId) ||
      currentLocation?.id === locationId;

    if (!isConnected) {
      setError('No puedes viajar a una ubicación no conectada');
      return;
    }

    setTraveling(true);
    setError('');

    try {
      const travelResult = await travelToLocation(locationId);

      const newLocation = locations.find(loc => loc.id === travelResult.current_location.id);
      setCurrentLocation(newLocation);
      setConnectedLocations(travelResult.connected_locations);

      const userData = await getCurrentUser();
      setUserMoney(userData.player_info?.money || 0);

    } catch (err) {
      setError(err.message || 'Error al viajar');
      console.error('Error traveling:', err);
    } finally {
      setTraveling(false);
    }
  };

  const handleHealTeam = async () => {
    try {
      setHealing(true);
      setHealingAnimation(true);
      setError('');

      await healTeam();

      setTimeout(async () => {
        await fetchTeamData();
        await fetchTeamAndReserveData();

        const userData = await getCurrentUser();
        setUserMoney(userData.player_info?.money || 0);

        setHealingAnimation(false);
        setHealing(false);

        setError('¡Equipo curado exitosamente!');
        setTimeout(() => setError(''), 3000);
      }, 2000);

    } catch (err) {
      setHealingAnimation(false);
      setHealing(false);
      setError(err.message || 'Error al curar el equipo');
    }
  };

  const handleBuyItem = async (itemId, itemPrice, itemName) => {
    if (userMoney < itemPrice) {
      setError(`No tienes suficiente dinero. Necesitas $${itemPrice} y tienes $${userMoney}`);
      setTimeout(() => setError(''), 3000);
      return;
    }

    try {
      setBuying(itemId);
      setError('');

      const result = await buyItem(itemId);

      await fetchShopItems();
      const userData = await getCurrentUser();
      setUserMoney(userData.player_info?.money || 0);
      const bagData = await getBag();
      setBag(bagData[0]);

      setError(`¡${itemName} comprado exitosamente por $${itemPrice}! Saldo restante: $${userData.player_info?.money || 0}`);
      setTimeout(() => setError(''), 3000);

    } catch (err) {
      setError(err.message || 'Error al comprar el item');
      setTimeout(() => setError(''), 3000);
    } finally {
      setBuying(null);
    }
  };

  const handleMoveToReserve = async (pokemonId, pokemonName) => {
    try {
      await moveToReserve(pokemonId);
      await fetchTeamData();
      await fetchTeamAndReserveData();
      setError(`${pokemonName} movido a la reserva`);
      setTimeout(() => setError(''), 3000);
    } catch (err) {
      setError('Error al mover Pokémon a reserva');
      console.error('Error moving to reserve:', err);
    }
  };

  const handleMoveToTeam = async (pokemonId, pokemonName) => {
    if (teamReserveData.team_count >= teamReserveData.max_team_size) {
      setError('El equipo está lleno. Mueve un Pokémon a la reserva primero.');
      setTimeout(() => setError(''), 3000);
      return;
    }

    try {
      await moveToTeam(pokemonId);
      await fetchTeamData();
      await fetchTeamAndReserveData();
      setError(`${pokemonName} movido al equipo`);
      setTimeout(() => setError(''), 3000);
    } catch (err) {
      setError('Error al mover Pokémon al equipo');
      console.error('Error moving to team:', err);
    }
  };

  const handleDragStart = (e, pokemonId) => {
    e.dataTransfer.setData('pokemonId', pokemonId.toString());
    e.currentTarget.style.opacity = '0.4';
  };

  const handleDragEnd = (e) => {
    e.currentTarget.style.opacity = '1';
    setDragOverIndex(null);
  };

  const handleDragOver = (e, index) => {
    e.preventDefault();
    setDragOverIndex(index);
  };

  const handleDragLeave = (e) => {
    setDragOverIndex(null);
  };

  const handleDrop = async (e, targetPosition) => {
    e.preventDefault();
    setDragOverIndex(null);

    const pokemonId = e.dataTransfer.getData('pokemonId');

    try {
      await movePokemonToPosition(parseInt(pokemonId), targetPosition);
      await fetchTeamData();
      await fetchTeamAndReserveData();
    } catch (err) {
      setError('Error al mover el Pokémon');
      console.error('Error moving pokemon:', err);
    }
  };

  const getHealthColor = (currentHp, maxHp) => {
    const percentage = (currentHp / maxHp) * 100;
    if (percentage <= 20) return '#e74c3c';
    else if (percentage <= 50) return '#f39c12';
    else return '#27ae60';
  };

  const calculateExpPercentage = (pokemon) => {
    if (pokemon.experience_info) {
      return pokemon.experience_info.progress_percentage;
    }
    const currentLevelExp = (pokemon.level - 1) * 100;
    const nextLevelExp = pokemon.level * 100;
    const progress = ((pokemon.experience - currentLevelExp) / (nextLevelExp - currentLevelExp)) * 100;
    return Math.min(Math.max(progress, 0), 100);
  };

  const getExpText = (pokemon) => {
    if (pokemon.experience_info) {
      const expInfo = pokemon.experience_info;
      return `${expInfo.exp_in_current_level}/${expInfo.exp_needed_for_next_level}`;
    }
    const currentLevelExp = (pokemon.level - 1) * 100;
    return `${pokemon.experience - currentLevelExp}/100`;
  };

  const getLocationTypeColor = (type) => {
    switch (type) {
      case 'town':
        return '#3498db';
      case 'route':
        return '#27ae60';
      default:
        return '#95a5a6';
    }
  };

  const getLocationTypeIcon = (type) => {
    switch (type) {
      case 'town':
        return '🏠';
      case 'route':
        return '🛣️';
      default:
        return '📍';
    }
  };

  const isLocationConnected = (locationId) => {
    if (!currentLocation) return false;
    if (locationId === currentLocation.id) return true;
    return connectedLocations.some(loc => loc.id === locationId);
  };

  const isPokemonDiscovered = (pokemonId) => {
    return pokedex.some(entry => entry.pokemon === pokemonId);
  };

  const getRarityDisplay = (rarity) => {
    switch (rarity) {
      case 'common':
        return 'Común';
      case 'uncommon':
        return 'Poco Común';
      case 'rare':
        return 'Raro';
      default:
        return rarity;
    }
  };

  const handleBackToDashboard = () => {
    navigate('/dashboard');
  };

  const openPokemonDetails = (pokemon) => {
    setSelectedPokemon(pokemon);
    setPokemonDetailTab('stats');
  };

  const closePokemonDetails = () => {
    setSelectedPokemon(null);
  };

  const handleTeachMove = async (moveId, moveName) => {
    if (!selectedPokemon || teachingMove) return;

    try {
      setTeachingMove(true);
      setError('');

      const result = await teachMove(selectedPokemon.id, moveId);

      const updatedPokemon = { ...selectedPokemon };
      updatedPokemon.moves = result.current_moves || [];
      
      if (selectedPokemon.available_moves) {
        const learnedMove = selectedPokemon.available_moves.find(move => move.id === moveId);
        if (learnedMove) {
          const moveDetail = {
            id: learnedMove.id,
            name: learnedMove.name,
            type: learnedMove.type,
            power: learnedMove.power,
            accuracy: learnedMove.accuracy,
            pp: learnedMove.pp,
            current_pp: learnedMove.pp,
            damage_class: learnedMove.damage_class
          };
          
          updatedPokemon.moves_details = [...(selectedPokemon.moves_details || []), moveDetail];
        }
      }

      setSelectedPokemon(updatedPokemon);
      setError(`¡${selectedPokemon.nickname || selectedPokemon.pokemon_name} aprendió ${moveName}!`);
      setTimeout(() => setError(''), 3000);

      await fetchTeamData();
      await fetchTeamAndReserveData();

    } catch (err) {
      setError(err.message || 'Error al enseñar el movimiento');
      console.error('Error teaching move:', err);
    } finally {
      setTeachingMove(false);
    }
  };

  const handleForgetMove = async (moveId, moveName) => {
    if (!selectedPokemon || forgettingMove) return;

    if (selectedPokemon.moves_details && selectedPokemon.moves_details.length <= 1) {
      setError('El Pokémon necesita tener al menos un movimiento');
      setTimeout(() => setError(''), 3000);
      return;
    }

    try {
      setForgettingMove(true);
      setError('');

      const result = await forgetMove(selectedPokemon.id, moveId);

      const updatedPokemon = { ...selectedPokemon };
      updatedPokemon.moves = result.current_moves || [];
      updatedPokemon.moves_details = (selectedPokemon.moves_details || []).filter(move => move.id !== moveId);

      setSelectedPokemon(updatedPokemon);
      setError(`¡${selectedPokemon.nickname || selectedPokemon.pokemon_name} olvidó ${moveName}!`);
      setTimeout(() => setError(''), 3000);

      await fetchTeamData();
      await fetchTeamAndReserveData();

    } catch (err) {
      setError(err.message || 'Error al olvidar el movimiento');
      console.error('Error forgetting move:', err);
    } finally {
      setForgettingMove(false);
    }
  };

  const renderWildPokemons = () => {
    if (!currentLocation || currentLocation.location_type === 'town' || !currentLocation.wild_pokemons || currentLocation.wild_pokemons.length === 0) {
      return null;
    }

    return (
      <div className="wild-pokemons-section">
        <div className="battle-options">
          <button
            className="battle-btn wild-pokemon-btn"
            onClick={() => navigate('/battle/wild')}
          >
            Buscar Pokémon Salvaje
          </button>

          <button
            className="battle-btn trainer-btn"
            onClick={() => navigate('/battle/trainer')}
          >
            Buscar Entrenador Pokémon
          </button>
        </div>

        <h3>Pokémon Salvajes en {currentLocation.name}</h3>
        <div className="pokemon-grid">
          {currentLocation.wild_pokemons.map((wildPokemon) => {
            const isDiscovered = isPokemonDiscovered(wildPokemon.pokemon);

            return (
              <div key={wildPokemon.id} className={`pokemon-card ${isDiscovered ? 'discovered' : 'undiscovered'}`}>
                <div className="pokemon-sprite">
                  {isDiscovered ? (
                    <img
                      src={`https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/${wildPokemon.pokemon}.png`}
                      alt={wildPokemon.pokemon_name}
                    />
                  ) : (
                    <div className="unknown-pokemon">
                      <div className="question-mark">?</div>
                    </div>
                  )}
                </div>
                <div className="pokemon-info">
                  <h4>{isDiscovered ? wildPokemon.pokemon_name : '?????'}</h4>
                  {isDiscovered && (
                    <>
                      <div className="pokemon-types">
                        {wildPokemon.pokemon_types.map(type => (
                          <span key={type} className={`type-badge type-${type}`}>
                            {type}
                          </span>
                        ))}
                      </div>
                      <div className="pokemon-details">
                        <span className="level-range">
                          Nv. {wildPokemon.min_level}-{wildPokemon.max_level}
                        </span>
                        <span className={`rarity rarity-${wildPokemon.rarity}`}>
                          {getRarityDisplay(wildPokemon.rarity)}
                        </span>
                      </div>
                    </>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  const renderPokemonCenter = () => {
    console.log('Rendering Pokemon Center with teamData:', teamData);

    return (
      <div className="pokemon-center-tab">
        <h3>Centro Pokémon de {currentLocation.name}</h3>
        <p className="center-description">Aquí podemos curar a todos tus Pokémon y dejarlos como nuevos.</p>

        {teamLoading ? (
          <div className="loading-center">
            <div className="loading-spinner small"></div>
            <p>Cargando equipo...</p>
          </div>
        ) : teamData.team && teamData.team.length > 0 ? (
          <div className="team-health-status">
            <h4>Estado de tu Equipo ({teamData.team_count}/{teamData.max_team_size}):</h4>
            <div className="pokemon-health-list">
              {teamData.team.map((pokemon) => (
                <div key={pokemon.id} className="pokemon-health-item">
                  <img src={pokemon.sprite_front} alt={pokemon.pokemon_name} className="health-pokemon-sprite" />
                  <div className="health-info">
                    <div className="pokemon-name-health">
                      <span className="pokemon-name">{pokemon.nickname || pokemon.pokemon_name}</span>
                      <span className="pokemon-level">Nv. {pokemon.level}</span>
                    </div>
                    <div className="health-bar-container">
                      <div className="health-bar">
                        <div className="bar">
                          <div
                            className={`health-fill ${healingAnimation ? 'healing' : ''}`}
                            style={{
                              width: `${(pokemon.current_hp / pokemon.hp) * 100}%`,
                              backgroundColor: getHealthColor(pokemon.current_hp, pokemon.hp)
                            }}
                          ></div>
                        </div>
                        <span className="hp-text">
                          {pokemon.current_hp}/{pokemon.hp} HP
                          {pokemon.current_hp < pokemon.hp && (
                            <span className="needs-healing"> (Necesita curación)</span>
                          )}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="empty-team-message">
            <p>No tienes Pokémon en tu equipo para curar.</p>
          </div>
        )}

        <button
          className="heal-button"
          onClick={handleHealTeam}
          disabled={healing || !teamData.team || teamData.team.length === 0}
        >
          {healing ? 'Curando...' : 'Curar Equipo Pokémon'}
        </button>

        {healingAnimation && (
          <div className="healing-animation">
            <div className="healing-sparkle">✨</div>
            <div className="healing-sparkle">✨</div>
            <div className="healing-sparkle">✨</div>
            <p className="healing-text">¡Curando a tus Pokémon!</p>
          </div>
        )}
      </div>
    );
  };

  const renderPokemonShop = () => {
    const getItemCount = (itemType) => {
      if (!bag || !bag.item_summary) return 0;

      switch (itemType) {
        case 'pokeball': return bag.item_summary.pokeballs || 0;
        case 'ultra_ball': return bag.item_summary.ultra_balls || 0;
        case 'potion': return bag.item_summary.potions || 0;
        case 'super_potion': return bag.item_summary.super_potions || 0;
        case 'hyper_potion': return bag.item_summary.hyper_potions || 0;
        default: return 0;
      }
    };

    const getItemTypeName = (itemType) => {
      switch (itemType) {
        case 'pokeball': return 'Pokéball';
        case 'ultra_ball': return 'Ultraball';
        case 'potion': return 'Poción';
        case 'super_potion': return 'Superpoción';
        case 'hyper_potion': return 'Hiperpoción';
        default: return itemType;
      }
    };

    return (
      <div className="shop-tab">
        <div className="shop-header">
          <h3>Tienda Pokémon de {currentLocation.name}</h3>
          <div className="money-display">
            <span className="money-label">Dinero disponible:</span>
            <span className="money-amount">${userMoney}</span>
          </div>
        </div>

        {shopLoading ? (
          <div className="loading-shop">
            <div className="loading-spinner small"></div>
            <p>Cargando items...</p>
          </div>
        ) : (
          <div className="shop-items-grid">
            {shopItems.map(item => {
              const itemCount = getItemCount(item.item_type);

              return (
                <div key={item.id} className="shop-item-card">
                  <div className="shop-item-info">
                    <h4>{item.name}</h4>
                    <p className="item-description">{item.description}</p>
                    <div className="item-details">
                      <span className="item-type">Tipo: {getItemTypeName(item.item_type)}</span>
                      <span className="item-effect">
                        {item.item_type.includes('potion') ? `Cura: ${item.effect_value} HP` :
                          item.item_type.includes('ball') ? `Multiplicador: ${item.effect_value}x` :
                            `Efecto: ${item.effect_value}`}
                      </span>
                      <span className="item-owned">En tu mochila: {itemCount}</span>
                    </div>
                  </div>
                  <div className="shop-item-action">
                    <span className="item-price">${item.price}</span>
                    <button
                      className="buy-button"
                      onClick={() => handleBuyItem(item.id, item.price, item.name)}
                      disabled={buying === item.id || userMoney < item.price}
                    >
                      {buying === item.id ? 'Comprando...' :
                        userMoney < item.price ? 'Saldo Insuficiente' : 'Comprar'}
                    </button>
                    {userMoney < item.price && (
                      <span className="insufficient-funds">Fondos insuficientes</span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    );
  };

  const renderTeam = () => {
    console.log('Rendering Team with teamReserveData:', teamReserveData);

    const { team, team_count, max_team_size } = teamReserveData;

    return (
      <div className="team-tab">
        <h3>Tu Equipo Pokémon ({team_count}/{max_team_size})</h3>
        <p className="team-instructions">Arrastra los Pokémon para cambiar su orden en el equipo</p>

        {teamLoading ? (
          <div className="loading-team">
            <div className="loading-spinner small"></div>
            <p>Cargando equipo...</p>
          </div>
        ) : team_count === 0 ? (
          <div className="empty-team">
            <p>No tienes Pokémon en tu equipo</p>
          </div>
        ) : (
          <div className="pokemon-grid">
            {team.map((pokemon, index) => (
              <div
                key={pokemon.id}
                className={`pokemon-card ${dragOverIndex === index ? 'drag-over' : ''}`}
                onClick={() => openPokemonDetails(pokemon)}
                draggable
                onDragStart={(e) => handleDragStart(e, pokemon.id)}
                onDragEnd={handleDragEnd}
                onDragOver={(e) => handleDragOver(e, index)}
                onDragLeave={handleDragLeave}
                onDrop={(e) => handleDrop(e, index)}
              >
                <div className="pokemon-position">Posición {index + 1}</div>
                <img src={pokemon.sprite_front} alt={pokemon.pokemon_name} />
                <h4>{pokemon.nickname || pokemon.pokemon_name}</h4>
                <p className="level">Nivel {pokemon.level}</p>
                <div className="types">
                  {pokemon.pokemon_types.map((type) => (
                    <span key={type} className={`type type-${type}`}>
                      {type}
                    </span>
                  ))}
                </div>
                <div className="health-bar">
                  <span>HP: {pokemon.current_hp}/{pokemon.hp}</span>
                  <div className="bar">
                    <div
                      className="health-fill"
                      style={{
                        width: `${(pokemon.current_hp / pokemon.hp) * 100}%`,
                        backgroundColor: getHealthColor(pokemon.current_hp, pokemon.hp)
                      }}
                    ></div>
                  </div>
                </div>
                <div className="exp-bar">
                  <span>EXP: {getExpText(pokemon)}</span>
                  <div className="bar">
                    <div
                      className="exp-fill"
                      style={{ width: `${calculateExpPercentage(pokemon)}%` }}
                    ></div>
                  </div>
                  <span className="exp-percentage">{calculateExpPercentage(pokemon).toFixed(0)}%</span>
                </div>
                <button
                  className="move-to-reserve-btn"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleMoveToReserve(pokemon.id, pokemon.nickname || pokemon.pokemon_name);
                  }}
                >
                  → Reserva
                </button>
              </div>
            ))}

            {Array.from({ length: max_team_size - team_count }, (_, index) => (
              <div key={`empty-${index}`} className="pokemon-card empty-slot">
                <div className="empty-slot-content">
                  <div className="empty-slot-icon">+</div>
                  <p>Espacio Vacío</p>
                  <small>Posición {team_count + index + 1}</small>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  const renderReserve = () => {
    console.log('Rendering Reserve with teamReserveData:', teamReserveData);

    const { reserve, reserve_count, team_count, max_team_size } = teamReserveData;

    return (
      <div className="reserve-tab">
        <h3>Reserva de Pokémon ({reserve_count})</h3>

        {reserve_count === 0 ? (
          <div className="empty-reserve">
            <p>No hay Pokémon en la reserva</p>
          </div>
        ) : (
          <div className="pokemon-grid">
            {reserve.map((pokemon) => (
              <div
                key={pokemon.id}
                className="pokemon-card"
                onClick={() => openPokemonDetails(pokemon)}
              >
                <img src={pokemon.sprite_front} alt={pokemon.pokemon_name} />
                <h4>{pokemon.nickname || pokemon.pokemon_name}</h4>
                <p className="level">Nivel {pokemon.level}</p>
                <div className="types">
                  {pokemon.pokemon_types.map((type) => (
                    <span key={type} className={`type type-${type}`}>
                      {type}
                    </span>
                  ))}
                </div>
                <div className="health-bar">
                  <span>HP: {pokemon.current_hp}/{pokemon.hp}</span>
                  <div className="bar">
                    <div
                      className="health-fill"
                      style={{
                        width: `${(pokemon.current_hp / pokemon.hp) * 100}%`,
                        backgroundColor: getHealthColor(pokemon.current_hp, pokemon.hp)
                      }}
                    ></div>
                  </div>
                </div>
                <div className="exp-bar">
                  <span>EXP: {getExpText(pokemon)}</span>
                  <div className="bar">
                    <div
                      className="exp-fill"
                      style={{ width: `${calculateExpPercentage(pokemon)}%` }}
                    ></div>
                  </div>
                  <span className="exp-percentage">{calculateExpPercentage(pokemon).toFixed(0)}%</span>
                </div>
                <button
                  className="move-to-team-btn"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleMoveToTeam(pokemon.id, pokemon.nickname || pokemon.pokemon_name);
                  }}
                  disabled={team_count >= max_team_size}
                >
                  {team_count >= max_team_size ? 'Equipo Lleno' : '→ Equipo'}
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  const renderTeamAndReserve = () => {
    return (
      <div className="team-reserve-tab">
        <div className="team-reserve-tabs">
          <button
            className={`team-reserve-tab-btn ${activeTeamTab === 'team' ? 'active' : ''}`}
            onClick={() => setActiveTeamTab('team')}
          >
            Equipo
          </button>
          <button
            className={`team-reserve-tab-btn ${activeTeamTab === 'reserve' ? 'active' : ''}`}
            onClick={() => setActiveTeamTab('reserve')}
          >
            Reserva
          </button>
        </div>

        <div className="team-reserve-content">
          {activeTeamTab === 'team' ? renderTeam() : renderReserve()}
        </div>
      </div>
    );
  };

  const renderCityServices = () => {
    if (currentLocation?.location_type !== 'town') return null;

    return (
      <div className="city-services-section">
        <div className="city-tabs">
          <button
            className={`city-tab ${activeCityTab === 'pokemon-center' ? 'active' : ''}`}
            onClick={() => setActiveCityTab('pokemon-center')}
          >
            Centro Pokémon
          </button>
          <button
            className={`city-tab ${activeCityTab === 'shop' ? 'active' : ''}`}
            onClick={() => setActiveCityTab('shop')}
          >
            Tienda Pokémon
          </button>
          <button
            className={`city-tab ${activeCityTab === 'team-reserve' ? 'active' : ''}`}
            onClick={() => setActiveCityTab('team-reserve')}
          >
            Equipo y Reserva
          </button>
        </div>

        <div className="city-tab-content">
          {activeCityTab === 'pokemon-center' && renderPokemonCenter()}
          {activeCityTab === 'shop' && renderPokemonShop()}
          {activeCityTab === 'team-reserve' && renderTeamAndReserve()}
        </div>
      </div>
    );
  };

  const renderLearnedMoves = () => {
    if (!selectedPokemon) return null;

    const movesDetails = selectedPokemon.moves_details || [];
    const emptySlots = 4 - movesDetails.length;

    return (
      <div className="learned-moves-section">
        <h4>Movimientos Aprendidos (Máx. 4)</h4>
        <div className="moves-grid">
          {movesDetails.map((move, index) => (
            <div key={move.id} className="move-slot">
              <div className="move-header">
                <span className="move-name">{move.name}</span>
                <span className={`move-type type-${move.type}`}>{move.type}</span>
              </div>
              <div className="move-info">
                <span className="move-power">
                  {move.power > 0 ? `Poder: ${move.power}` : 'Movimiento de Estado'}
                </span>
                <span className="move-accuracy">Precisión: {move.accuracy}%</span>
                <span className="move-pp">PP: {move.current_pp}/{move.pp}</span>
              </div>
              <div className="move-class">
                Clase: {move.damage_class === 'physical' ? 'Físico' :
                  move.damage_class === 'special' ? 'Especial' : 'Estado'}
              </div>
              <button
                className="forget-move-btn"
                onClick={() => handleForgetMove(move.id, move.name)}
                disabled={forgettingMove || movesDetails.length <= 1}
              >
                {forgettingMove ? 'Olvidando...' : 'Olvidar Movimiento'}
              </button>
            </div>
          ))}

          {Array.from({ length: emptySlots }, (_, index) => (
            <div key={`empty-${index}`} className="move-slot empty-move-slot">
              <div className="empty-slot-content">
                <div className="empty-slot-icon">+</div>
                <p>Espacio Vacío</p>
                <small>Slot {movesDetails.length + index + 1}</small>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderAvailableMoves = () => {
    if (!selectedPokemon || !selectedPokemon.available_moves) {
      return (
        <div className="no-available-moves">
          <p>No hay movimientos disponibles para aprender en este nivel.</p>
        </div>
      );
    }

    const availableMoves = selectedPokemon.available_moves || [];
    const currentMoves = selectedPokemon.moves || [];

    return (
      <div className="available-moves-section">
        <h4>Movimientos Disponibles para Aprender</h4>
        <div className="moves-grid">
          {availableMoves.map((move) => {
            const isAlreadyKnown = move.already_known || currentMoves.includes(move.id);
            const canLearn = selectedPokemon.moves_details && selectedPokemon.moves_details.length < 4;

            return (
              <div key={move.id} className={`move-slot ${isAlreadyKnown ? 'already-known' : ''}`}>
                <div className="move-header">
                  <span className="move-name">{move.name}</span>
                  <span className={`move-type type-${move.type}`}>{move.type}</span>
                </div>
                <div className="move-info">
                  <span className="move-power">
                    {move.power > 0 ? `Poder: ${move.power}` : 'Movimiento de Estado'}
                  </span>
                  <span className="move-accuracy">Precisión: {move.accuracy}%</span>
                  <span className="move-pp">PP: {move.pp}</span>
                  <span className="move-learn-level">Nivel: {move.level_learned}</span>
                </div>
                <div className="move-class">
                  Clase: {move.damage_class === 'physical' ? 'Físico' :
                    move.damage_class === 'special' ? 'Especial' : 'Estado'}
                </div>
                {isAlreadyKnown ? (
                  <button className="already-known-btn" disabled>
                    Ya Aprendido
                  </button>
                ) : (
                  <button
                    className="teach-move-btn"
                    onClick={() => handleTeachMove(move.id, move.name)}
                    disabled={teachingMove || !canLearn}
                  >
                    {teachingMove ? 'Enseñando...' : 'Aprender Movimiento'}
                  </button>
                )}
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  const renderPokemonDetailsModal = () => {
    if (!selectedPokemon) return null;

    return (
      <div className="modal-overlay" onClick={closePokemonDetails}>
        <div className="pokemon-modal" onClick={(e) => e.stopPropagation()}>
          <div className="modal-header">
            <h2>{selectedPokemon.nickname || selectedPokemon.pokemon_name}</h2>
            <button className="close-btn" onClick={closePokemonDetails}>×</button>
          </div>

          <div className="modal-content">
            <div className="pokemon-basic-info">
              <img src={selectedPokemon.sprite_front} alt={selectedPokemon.pokemon_name} />
              <div className="basic-details">
                <p className="level">Nivel {selectedPokemon.level}</p>
                <div className="types">
                  {selectedPokemon.pokemon_types.map((type) => (
                    <span key={type} className={`type type-${type}`}>
                      {type}
                    </span>
                  ))}
                </div>
                <div className="health-bar">
                  <span>HP: {selectedPokemon.current_hp}/{selectedPokemon.hp}</span>
                  <div className="bar">
                    <div
                      className="health-fill"
                      style={{
                        width: `${(selectedPokemon.current_hp / selectedPokemon.hp) * 100}%`,
                        backgroundColor: getHealthColor(selectedPokemon.current_hp, selectedPokemon.hp)
                      }}
                    ></div>
                  </div>
                </div>
                <div className="exp-bar">
                  <span>EXP: {getExpText(selectedPokemon)}</span>
                  <div className="bar">
                    <div
                      className="exp-fill"
                      style={{ width: `${calculateExpPercentage(selectedPokemon)}%` }}
                    ></div>
                  </div>
                  <span className="exp-percentage">{calculateExpPercentage(selectedPokemon).toFixed(0)}%</span>
                </div>
              </div>
            </div>

            <div className="modal-tabs">
              <button
                className={`tab ${pokemonDetailTab === 'stats' ? 'active' : ''}`}
                onClick={() => setPokemonDetailTab('stats')}
              >
                Estadísticas
              </button>
              <button
                className={`tab ${pokemonDetailTab === 'moves' ? 'active' : ''}`}
                onClick={() => setPokemonDetailTab('moves')}
              >
                Movimientos
              </button>
            </div>

            <div className="tab-content">
              {pokemonDetailTab === 'stats' && (
                <div className="stats-tab">
                  <h3>Estadísticas Base</h3>
                  <div className="stats-grid-detailed">
                    <div className="stat-item-detailed">
                      <span className="stat-label">HP</span>
                      <span className="stat-value">{selectedPokemon.hp}</span>
                    </div>
                    <div className="stat-item-detailed">
                      <span className="stat-label">Ataque</span>
                      <span className="stat-value">{selectedPokemon.attack}</span>
                    </div>
                    <div className="stat-item-detailed">
                      <span className="stat-label">Defensa</span>
                      <span className="stat-value">{selectedPokemon.defense}</span>
                    </div>
                    <div className="stat-item-detailed">
                      <span className="stat-label">Ataque Especial</span>
                      <span className="stat-value">{selectedPokemon.special_attack}</span>
                    </div>
                    <div className="stat-item-detailed">
                      <span className="stat-label">Defensa Especial</span>
                      <span className="stat-value">{selectedPokemon.special_defense}</span>
                    </div>
                    <div className="stat-item-detailed">
                      <span className="stat-label">Velocidad</span>
                      <span className="stat-value">{selectedPokemon.speed}</span>
                    </div>
                  </div>
                </div>
              )}

              {pokemonDetailTab === 'moves' && (
                <div className="moves-tab">
                  {renderLearnedMoves()}
                  {renderAvailableMoves()}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderKantoMap = () => {
    const mapGrid = [
      // Fila 1
      [{ id: 4, name: "Ciudad Azulona", type: "town" }, null, null, null, null, null, null, null],

      // Fila 2
      [{ id: 16, name: "Ruta 5", type: "route" }, { id: 5, name: "Ciudad Carmín", type: "town" }, { id: 18, name: "Ruta 7", type: "route" }, { id: 19, name: "Ruta 8", type: "route" }, { id: 20, name: "Ruta 9", type: "route" }, { id: 6, name: "Ciudad Azafrán", type: "town" }, { id: 21, name: "Ruta 10", type: "route" }, { id: 22, name: "Ruta 11", type: "route" }],

      // Fila 3
      [{ id: 15, name: "Ruta 4", type: "route" }, { id: 17, name: "Ruta 6", type: "route" }, null, { id: 26, name: "Ruta 15", type: "route" }, { id: 9, name: "Ciudad Canela", type: "town" }, { id: 24, name: "Ruta 13", type: "route" }, null, null],

      // Fila 4
      [{ id: 14, name: "Ruta 3", type: "route" }, { id: 3, name: "Ciudad Lavanda", type: "town" }, null, null, { id: 25, name: "Ruta 14", type: "route" }, { id: 8, name: "Pueblo Verde", type: "town" }, { id: 23, name: "Ruta 12", type: "route" }, { id: 7, name: "Ciudad Fucsia", type: "town" }],

      // Fila 5
      [null, { id: 13, name: "Ruta 2", type: "route" }, null, { id: 27, name: "Ruta 16", type: "route" }, null, { id: 31, name: "Ruta 20", type: "route" }, null, null],

      // Fila 6
      [null, { id: 2, name: "Ciudad Celeste", type: "town" }, null, null, null, { id: 11, name: "Ciudad Plateada", type: "town" }, { id: 30, name: "Ruta 19", type: "route" }, { id: 29, name: "Ruta 18", type: "route" },],

      // Fila 7
      [null, { id: 12, name: "Ruta 1", type: "route" }, null, { id: 28, name: "Ruta 17", type: "route" }, null, null, null, null],

      // Fila 8
      [null, { id: 1, name: "Pueblo Paleta", type: "town" }, null, { id: 10, name: "Ciudad Espuma", type: "town" }, null, { id: 34, name: "Ruta 23", type: "route" }, { id: 33, name: "Ruta 22", type: "route" }, { id: 32, name: "Ruta 21", type: "route" }]
    ];

    return (
      <div className="map-table">
        {mapGrid.map((row, rowIndex) => (
          <div key={rowIndex} className="map-row">
            {row.map((location, colIndex) => (
              <div key={colIndex} className="map-cell">
                {location ? (
                  <div
                    className={`map-location ${location.type} ${currentLocation?.id === location.id ? 'current' : ''
                      } ${isLocationConnected(location.id) ? 'connected' : 'not-connected'}`}
                    onClick={() => handleTravel(location.id)}
                  >
                    {currentLocation?.id === location.id && (
                      <div className="player-marker">★</div>
                    )}
                    <div className="location-name">
                      {location.name}
                    </div>
                    <div className="location-icon">
                      {getLocationTypeIcon(location.type)}
                    </div>
                    {traveling && isLocationConnected(location.id) && location.id !== currentLocation?.id && (
                      <div className="traveling-overlay">Viajando...</div>
                    )}
                  </div>
                ) : (
                  <div className="empty-cell"></div>
                )}
              </div>
            ))}
          </div>
        ))}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="loading-spinner"></div>
        <p>Cargando mapa...</p>
      </div>
    );
  }

  return (
    <div className="game-screen">
      <div className="game-container">
        <div className="game-header">

          <div className="header-content">
            <button
              className="back-button"
              onClick={handleBackToDashboard}
            >
              ← Volver al Dashboard
            </button>

          </div>

          <h1>Mapa de Kanto</h1>
          <div className="current-location-info">
            {currentLocation && (
              <div className="location-card current">
                <span className="location-icon">
                  {getLocationTypeIcon(currentLocation.location_type)}
                </span>
                <div className="location-details">
                  <h3>{currentLocation.name}</h3>
                  <span
                    className="location-type"
                    style={{ color: getLocationTypeColor(currentLocation.location_type) }}
                  >
                    {currentLocation.location_type === 'town' ? 'Pueblo' : 'Ruta'}
                  </span>
                </div>
                <div className="you-are-here">¡Estás aquí!</div>
              </div>
            )}
          </div>
        </div>

        {error && <div className="error-message">{error}</div>}

        {traveling && (
          <div className="traveling-message">
            <div className="loading-spinner"></div>
            <p>Viajando...</p>
          </div>
        )}

        <div className="map-container">
          <h2>Mapa de la Región</h2>
          <p className="map-instructions">
            Haz clic en cualquier ubicación conectada (a color) para viajar allí
          </p>
          <div className="map-visual">
            {renderKantoMap()}
          </div>
        </div>

        {renderWildPokemons()}

        {renderCityServices()}

        {renderPokemonDetailsModal()}
      </div>
    </div>
  );
};

export default GameScreen;