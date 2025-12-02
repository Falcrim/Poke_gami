import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Navbar from './components/Navbar/Navbar';
import Login from './pages/Login/Login';
import Register from './pages/Register/Register';
import StarterSelection from './pages/StarterSelection/StarterSelection';
import Dashboard from './pages/Dashboard/Dashboard';
import Pokedex from './pages/Pokedex/Pokedex';
import Profile from './pages/Profile/Profile';
import Ranking from './pages/Ranking/Ranking';
import GameScreen from './pages/GameScreen/GameScreen';
import BattleScreen from './components/battle/BattleScreen';
import { getToken, getUser, setUser, removeToken, removeUser } from './utils/auth';
import { getCurrentUser } from './services/authService';
import './App.css';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUserState] = useState(null);
  const [loading, setLoading] = useState(true);
  const [shouldSelectStarter, setShouldSelectStarter] = useState(false);

  useEffect(() => {
    const initializeAuth = async () => {
      const token = getToken();
      const storedUser = getUser();

      if (token) {
        if (storedUser) {
          setUserState(storedUser);
          setIsAuthenticated(true);
        }

        try {
          const currentUser = await getCurrentUser();
          setUser(currentUser);
          setUserState(currentUser);
          setIsAuthenticated(true);
          
          if (!currentUser.player_info?.starter_chosen) {
            setShouldSelectStarter(true);
          }
        } catch (error) {
          console.error('Error verifying token:', error);
          removeToken();
          removeUser();
          setIsAuthenticated(false);
          setUserState(null);
        }
      } else {
        removeToken();
        removeUser();
        setIsAuthenticated(false);
        setUserState(null);
      }

      setLoading(false);
    };

    initializeAuth();
  }, []);

  const handleLogin = (userData) => {
    setIsAuthenticated(true);
    setUserState(userData);
    if (!userData.player_info?.starter_chosen) {
      setShouldSelectStarter(true);
    }
  };

  const handleStarterSelected = () => {
    setShouldSelectStarter(false);
  };

  const handleLogout = () => {
    removeToken();
    removeUser();
    setIsAuthenticated(false);
    setUserState(null);
    setShouldSelectStarter(false);
  };

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="loading-spinner"></div>
        <p>Cargando Pokémon...</p>
      </div>
    );
  }

  return (
    <Router>
      <div className="App">
        {isAuthenticated && <Navbar user={user} onLogout={handleLogout} />}
        <Routes>
          <Route
            path="/login"
            element={
              !isAuthenticated ?
                <Login onLogin={handleLogin} /> :
                shouldSelectStarter ? 
                  <Navigate to="/starter-selection" replace /> :
                  <Navigate to="/dashboard" replace />
            }
          />
          <Route
            path="/register"
            element={
              !isAuthenticated ?
                <Register onLogin={handleLogin} /> :
                shouldSelectStarter ? 
                  <Navigate to="/starter-selection" replace /> :
                  <Navigate to="/dashboard" replace />
            }
          />
          <Route
            path="/starter-selection"
            element={
              isAuthenticated && shouldSelectStarter ?
                <StarterSelection onStarterSelected={handleStarterSelected} /> :
                isAuthenticated ? 
                  <Navigate to="/dashboard" replace /> :
                  <Navigate to="/login" replace />
            }
          />
          <Route
            path="/dashboard"
            element={
              isAuthenticated && !shouldSelectStarter ?
                <Dashboard user={user} /> :
                isAuthenticated ? 
                  <Navigate to="/starter-selection" replace /> :
                  <Navigate to="/login" replace />
            }
          />
          <Route
            path="/pokedex"
            element={
              isAuthenticated && !shouldSelectStarter ?
                <Pokedex /> :
                isAuthenticated ? 
                  <Navigate to="/starter-selection" replace /> :
                  <Navigate to="/login" replace />
            }
          />
          <Route
            path="/profile"
            element={
              isAuthenticated && !shouldSelectStarter ?
                <Profile user={user} /> :
                isAuthenticated ? 
                  <Navigate to="/starter-selection" replace /> :
                  <Navigate to="/login" replace />
            }
          />
          <Route
            path="/ranking"
            element={
              isAuthenticated && !shouldSelectStarter ?
                <Ranking /> :
                isAuthenticated ? 
                  <Navigate to="/starter-selection" replace /> :
                  <Navigate to="/login" replace />
            }
          />
          <Route
            path="/game"
            element={
              isAuthenticated && !shouldSelectStarter ?
                <GameScreen /> :
                isAuthenticated ? 
                  <Navigate to="/starter-selection" replace /> :
                  <Navigate to="/login" replace />
            }
          />
          <Route
            path="/battle/:battleType"
            element={
              isAuthenticated && !shouldSelectStarter ?
                <BattleScreen /> :
                isAuthenticated ? 
                  <Navigate to="/starter-selection" replace /> :
                  <Navigate to="/login" replace />
            }
          />
          <Route
            path="/"
            element={
              isAuthenticated ?
                (shouldSelectStarter ? 
                  <Navigate to="/starter-selection" replace /> :
                  <Navigate to="/dashboard" replace />) :
                <Navigate to="/login" replace />
            }
          />
        </Routes>
      </div>
    </Router>
  );
}

export default App;