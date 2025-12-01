import React, { useState, useEffect } from 'react';
import { getRanking, getMyRanking } from '../../services/gameService';
import './Ranking.css';

const Ranking = () => {
  const [globalRanking, setGlobalRanking] = useState([]);
  const [myRanking, setMyRanking] = useState(null);
  const [activeTab, setActiveTab] = useState('global');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchRankings = async () => {
      try {
        const [globalData, myData] = await Promise.all([
          getRanking(),
          getMyRanking()
        ]);
        setGlobalRanking(globalData);
        setMyRanking(myData);
      } catch (err) {
        setError('Error al cargar los rankings');
      } finally {
        setLoading(false);
      }
    };

    fetchRankings();
  }, []);

  if (loading) {
    return <div className="loading">Cargando rankings...</div>;
  }

  return (
    <div className="ranking">
      <div className="ranking-container">
        <h1>Ranking de Entrenadores</h1>
        
        <div className="tabs">
          <button 
            className={`tab ${activeTab === 'global' ? 'active' : ''}`}
            onClick={() => setActiveTab('global')}
          >
            Ranking Global
          </button>
          <button 
            className={`tab ${activeTab === 'personal' ? 'active' : ''}`}
            onClick={() => setActiveTab('personal')}
          >
            Competidores Cercanos
          </button>
        </div>

        {error && <div className="error-message">{error}</div>}

        {activeTab === 'global' && (
          <div className="ranking-section">
            <h2>Ranking Global PVP</h2>
            <div className="ranking-table">
              <div className="table-header">
                <span>Posición</span>
                <span>Entrenador</span>
                <span>Rating</span>
                <span>Victorias</span>
                <span>Derrotas</span>
                <span>% Victoria</span>
              </div>
              {globalRanking.map((player) => (
                <div key={player.position} className="table-row">
                  <span className="position">#{player.position}</span>
                  <span className="username">{player.username}</span>
                  <span className="rating">{player.pvp_rating}</span>
                  <span className="wins">{player.battles_won}</span>
                  <span className="losses">{player.battles_lost}</span>
                  <span className="win-rate">
                    {player.win_rate > 0 ? player.win_rate.toFixed(1) : 0}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'personal' && myRanking && (
          <div className="ranking-section">
            <h2>Tus Estadísticas</h2>
            <div className="personal-stats">
              <div className="stat">
                <label>Tu Posición</label>
                <span className="value highlight">#{myRanking.user_stats.position}</span>
              </div>
              <div className="stat">
                <label>Rating PVP</label>
                <span className="value">{myRanking.user_stats.pvp_rating}</span>
              </div>
              <div className="stat">
                <label>Victorias</label>
                <span className="value win">{myRanking.user_stats.battles_won}</span>
              </div>
              <div className="stat">
                <label>Derrotas</label>
                <span className="value lose">{myRanking.user_stats.battles_lost}</span>
              </div>
              <div className="stat">
                <label>% Victoria</label>
                <span className="value">
                  {myRanking.user_stats.win_rate > 0 ? myRanking.user_stats.win_rate.toFixed(1) : 0}%
                </span>
              </div>
              <div className="stat">
                <label>Total Entrenadores</label>
                <span className="value">{myRanking.user_stats.total_players}</span>
              </div>
            </div>

            <h3>Competidores Cercanos</h3>
            <div className="nearby-ranking">
              {myRanking.nearby_players.map((player) => (
                <div 
                  key={player.position} 
                  className={`nearby-player ${player.is_current_user ? 'current-user' : ''}`}
                >
                  <span className="position">#{player.position}</span>
                  <span className="username">
                    {player.username}
                    {player.is_current_user && <span className="you-label"> (Tú)</span>}
                  </span>
                  <span className="rating">{player.pvp_rating}</span>
                  <span className="record">
                    {player.battles_won}W - {player.battles_lost}L
                  </span>
                  <span className="win-rate">
                    {player.win_rate > 0 ? player.win_rate.toFixed(1) : 0}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Ranking;