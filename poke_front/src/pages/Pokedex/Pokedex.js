import React, { useState, useEffect } from 'react';
import { getPokedex } from '../../services/gameService';
import './Pokedex.css';

const Pokedex = () => {
  const [pokedex, setPokedex] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchPokedex = async () => {
      try {
        const data = await getPokedex();
        setPokedex(data);
      } catch (err) {
        setError('Error al cargar la Pokédex');
      } finally {
        setLoading(false);
      }
    };

    fetchPokedex();
  }, []);

  const calculatePokedexStats = () => {
    const totalPokemon = 151;
    const caught = pokedex.filter(p => p.state === 'caught').length;
    const seen = pokedex.filter(p => p.state === 'seen' || p.state === 'caught').length;
    const completionPercentage = ((caught / totalPokemon) * 100).toFixed(2);
    
    return {
      total: totalPokemon,
      caught,
      seen,
      completionPercentage
    };
  };

  const pokedexStats = calculatePokedexStats();

  const getStateColor = (state) => {
    switch (state) {
      case 'caught':
        return '#27ae60';
      case 'seen':
        return '#f39c12';
      default:
        return '#7f8c8d';
    }
  };

  const getStateText = (state) => {
    switch (state) {
      case 'caught':
        return 'Capturado';
      case 'seen':
        return 'Visto';
      default:
        return 'Desconocido';
    }
  };

  if (loading) {
    return <div className="loading">Cargando Pokédex...</div>;
  }

  return (
    <div className="pokedex">
      <div className="pokedex-container">
        <h1>Pokédex</h1>
        
        <div className="pokedex-header">
          <div className="pokedex-stats">
            <div className="stat-item">
              <div className="stat-number">{pokedexStats.caught}</div>
              <div className="stat-label">Capturados</div>
            </div>
            <div className="stat-item">
              <div className="stat-number">{pokedexStats.seen}</div>
              <div className="stat-label">Vistos</div>
            </div>
            <div className="stat-item">
              <div className="stat-number">{pokedexStats.total}</div>
              <div className="stat-label">Total</div>
            </div>
            <div className="stat-item">
              <div className="stat-number">{pokedexStats.completionPercentage}%</div>
              <div className="stat-label">Completado</div>
            </div>
          </div>
          
          <div className="pokedex-progress">
            <div className="progress-header">
              <span>Progreso: {pokedexStats.caught} / {pokedexStats.total}</span>
              <span>{pokedexStats.completionPercentage}%</span>
            </div>
            <div className="progress-bar">
              <div 
                className="progress-fill"
                style={{ width: `${pokedexStats.completionPercentage}%` }}
              ></div>
            </div>
            <div className="progress-details">
              <div className="progress-detail">
                <span className="detail-label">Capturados:</span>
                <span className="detail-value caught">{pokedexStats.caught}</span>
              </div>
              <div className="progress-detail">
                <span className="detail-label">Vistos:</span>
                <span className="detail-value seen">{pokedexStats.seen}</span>
              </div>
              <div className="progress-detail">
                <span className="detail-label">Faltantes:</span>
                <span className="detail-value missing">{pokedexStats.total - pokedexStats.seen}</span>
              </div>
            </div>
          </div>
        </div>

        {error && <div className="error-message">{error}</div>}
        
        <div className="pokedex-grid">
          {Array.from({ length: 151 }, (_, index) => {
            const pokemonId = index + 1;
            const pokemonData = pokedex.find(p => p.pokemon === pokemonId);
            
            return (
              <div key={pokemonId} className="pokedex-card">
                <div className="pokemon-number">#{pokemonId.toString().padStart(3, '0')}</div>
                
                {pokemonData ? (
                  <>
                    <img 
                      src={pokemonData.sprite_front} 
                      alt={pokemonData.pokemon_name}
                      className="pokemon-sprite"
                    />
                    <h3 className="pokemon-name">{pokemonData.pokemon_name}</h3>
                    <div className="types">
                      {pokemonData.pokemon_types.map((type) => (
                        <span key={type} className={`type type-${type}`}>
                          {type}
                        </span>
                      ))}
                    </div>
                    <div 
                      className="state-badge"
                      style={{ backgroundColor: getStateColor(pokemonData.state) }}
                    >
                      {getStateText(pokemonData.state)}
                    </div>
                    {pokemonData.date_registered && (
                      <div className="date-registered">
                        Registrado: {new Date(pokemonData.date_registered).toLocaleDateString()}
                      </div>
                    )}
                  </>
                ) : (
                  <>
                    <div className="unknown-sprite">?</div>
                    <h3 className="pokemon-name unknown">Pokémon Desconocido</h3>
                    <div className="state-badge" style={{ backgroundColor: '#7f8c8d' }}>
                      Desconocido
                    </div>
                  </>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default Pokedex;