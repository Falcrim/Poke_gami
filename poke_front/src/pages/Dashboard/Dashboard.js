import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getTeamOrder, movePokemonToPosition } from '../../services/gameService';
import './Dashboard.css';

const Dashboard = ({ user }) => {
  const [teamData, setTeamData] = useState({ team: [], team_count: 0, max_team_size: 6 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedPokemon, setSelectedPokemon] = useState(null);
  const [activeTab, setActiveTab] = useState('stats');
  const [dragOverIndex, setDragOverIndex] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchTeam = async () => {
      try {
        const data = await getTeamOrder();
        setTeamData(data);
      } catch (err) {
        setError('Error al cargar el equipo Pokémon');
      } finally {
        setLoading(false);
      }
    };

    fetchTeam();
  }, []);

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

  const getHealthColor = (currentHp, maxHp) => {
    const percentage = (currentHp / maxHp) * 100;

    if (percentage <= 20) {
      return '#e74c3c';
    } else if (percentage <= 50) {
      return '#f39c12';
    } else {
      return '#27ae60';
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
      const response = await movePokemonToPosition(parseInt(pokemonId), targetPosition);

      const updatedTeam = [...teamData.team];
      const movedPokemonIndex = updatedTeam.findIndex(p => p.id === parseInt(pokemonId));

      if (movedPokemonIndex !== -1) {
        const [movedPokemon] = updatedTeam.splice(movedPokemonIndex, 1);
        updatedTeam.splice(targetPosition, 0, movedPokemon);

        const reorderedTeam = updatedTeam.map((pokemon, index) => ({
          ...pokemon,
          order: index
        }));

        setTeamData({
          ...teamData,
          team: reorderedTeam
        });
      }

    } catch (err) {
      setError('Error al mover el Pokémon');
      console.error('Error moving pokemon:', err);
    }
  };

  const openPokemonDetails = (pokemon) => {
    setSelectedPokemon(pokemon);
    setActiveTab('stats');
  };

  const closePokemonDetails = () => {
    setSelectedPokemon(null);
  };

  if (loading) {
    return <div className="loading">Cargando Pokémon...</div>;
  }

  const { team, team_count, max_team_size } = teamData;

  return (
    <div className="dashboard">
      <div className="dashboard-container">
        <div className="welcome-section">
          <h1>Bienvenido, {user?.username}!</h1>
          <div className="stats-grid">
            <div className="stat-card">
              <h3>Pokémon Capturados</h3>
              <p className="stat-number">{user?.pokedex_stats?.caught || 0}</p>
            </div>
            <div className="stat-card">
              <h3>Combates Ganados</h3>
              <p className="stat-number">{user?.battles_won || 0}</p>
            </div>
            <div className="stat-card">
              <h3>Rating PVP</h3>
              <p className="stat-number">{user?.pvp_rating || 0}</p>
            </div>
            <div className="stat-card">
              <h3>Dinero</h3>
              <p className="stat-number">${user?.player_info?.money || 0}</p>
            </div>
          </div>
        </div>

        <div className="adventure-section">
          <button
            className="adventure-btn"
            onClick={() => navigate('/game')}
          >
            Empezar Aventura
          </button>
        </div>
        <br />

        <div className="pokemon-section">
          <h2>Tu Equipo Pokémon ({team_count}/{max_team_size})</h2>
          <p className="team-instructions">Arrastra los Pokémon para cambiar su orden en el equipo</p>
          {error && <div className="error-message">{error}</div>}

          {team_count === 0 ? (
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
                  <h3>{pokemon.nickname || pokemon.pokemon_name}</h3>
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

        {selectedPokemon && (
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
                      <div className="bar" style={{ height: '12px', borderRadius: '6px' }}>
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
                    className={`tab ${activeTab === 'stats' ? 'active' : ''}`}
                    onClick={() => setActiveTab('stats')}
                  >
                    Estadísticas
                  </button>
                  <button
                    className={`tab ${activeTab === 'moves' ? 'active' : ''}`}
                    onClick={() => setActiveTab('moves')}
                  >
                    Movimientos
                  </button>
                </div>

                <div className="tab-content">
                  {activeTab === 'stats' && (
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

                  {activeTab === 'moves' && (
                    <div className="moves-tab">
                      <h3>Movimientos Aprendidos</h3>
                      <div className="moves-list">
                        {selectedPokemon.moves_details.map((move) => (
                          <div key={move.id} className="move-detail">
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
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;