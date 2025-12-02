import React from 'react';
import './Profile.css';

const Profile = ({ user }) => {
  if (!user) {
    return <div className="loading">Cargando perfil...</div>;
  }

  return (
    <div className="profile">
      <div className="profile-container">
        <div className="profile-header">
          <h1>Perfil de {user.username}</h1>
          <div className="profile-badge">Entrenador Pokémon</div>
        </div>

        <div className="profile-content">
          <div className="profile-section">
            <h2>Información del Entrenador</h2>
            <div className="info-grid">
              <div className="info-item">
                <label>Usuario:</label>
                <span>{user.username}</span>
              </div>
              <div className="info-item">
                <label>Email:</label>
                <span>{user.email}</span>
              </div>
              <div className="info-item">
                <label>Fecha de Registro:</label>
                <span>{new Date(user.date_joined).toLocaleDateString()}</span>
              </div>
              <div className="info-item">
                <label>Ubicación Actual:</label>
                <span>{user.player_info?.current_location?.name || 'Desconocida'}</span>
              </div>
            </div>
          </div>

          <div className="profile-section">
            <h2>Estadísticas de Batalla</h2>
            <div className="stats-grid">
              <div className="stat-item">
                <label>Combates Ganados</label>
                <span className="stat-value win">{user.battles_won}</span>
              </div>
              <div className="stat-item">
                <label>Combates Perdidos</label>
                <span className="stat-value lose">{user.battles_lost}</span>
              </div>
              <div className="stat-item">
                <label>Rating PVP</label>
                <span className="stat-value rating">{user.pvp_rating}</span>
              </div>
              <div className="stat-item">
                <label>Porcentaje de Victoria</label>
                <span className="stat-value">
                  {user.battles_won + user.battles_lost > 0 
                    ? Math.round((user.battles_won / (user.battles_won + user.battles_lost)) * 100)
                    : 0
                  }%
                </span>
              </div>
            </div>
          </div>

          <div className="profile-section">
            <h2>Progreso de la Pokédex</h2>
            <div className="pokedex-progress">
              <div className="progress-header">
                <span>Completado: {user.pokedex_stats?.completion_percentage?.toFixed(2) || 0}%</span>
                <span>{user.pokedex_stats?.caught || 0} / {user.pokedex_stats?.total_pokemon || 151}</span>
              </div>
              <div className="progress-bar">
                <div 
                  className="progress-fill"
                  style={{ 
                    width: `${user.pokedex_stats?.completion_percentage || 0}%` 
                  }}
                ></div>
              </div>
              <div className="progress-details">
                <div className="progress-item">
                  <span className="label">Vistos:</span>
                  <span className="value">{user.pokedex_stats?.seen || 0}</span>
                </div>
                <div className="progress-item">
                  <span className="label">Capturados:</span>
                  <span className="value">{user.pokedex_stats?.caught || 0}</span>
                </div>
              </div>
            </div>
          </div>

          <div className="profile-section">
            <h2>Información del Jugador</h2>
            <div className="player-info">
              <div className="info-item">
                <label>Dinero:</label>
                <span className="money">${user.player_info?.money || 0}</span>
              </div>
              <div className="info-item">
                <label>Pokémon en Equipo:</label>
                <span>{user.player_info?.team_count || 0}/6</span>
              </div>
              <div className="info-item">
                <label>Total Pokémon:</label>
                <span>{user.player_info?.pokemon_count || 0}</span>
              </div>
              <div className="info-item">
                <label>Posición en Ranking:</label>
                <span className="ranking-pos">#{user.ranking_position || 'N/A'}</span>
              </div>
            </div>
          </div>

          {user.achievements && user.achievements.length > 0 && (
            <div className="profile-section">
              <h2>Logros</h2>
              <div className="achievements-grid">
                {user.achievements.map((achievement, index) => (
                  <div key={index} className="achievement-card">
                    <h3>{achievement.name}</h3>
                    <p>{achievement.description}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Profile;