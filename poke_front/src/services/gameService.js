// services/gameService.js - ELIMINA las funciones de combate de aquí
import { apiRequest } from './api';

// Mantén solo las funciones de juego generales
export const getStarters = async () => {
  return await apiRequest('/game/pokemons/starters/');
};

export const getPlayerPokemons = async () => {
  return await apiRequest('/auth/player-pokemons/');
};

export const getPokedex = async () => {
  return await apiRequest('/auth/pokedex');
};

export const getRanking = async () => {
  return await apiRequest('/auth/users/ranking/');
};

export const getMyRanking = async () => {
  return await apiRequest('/auth/users/my_ranking/');
};

export const getTeamOrder = async () => {
  return await apiRequest('/auth/team-order/get_team_order/');
};

export const movePokemonToPosition = async (pokemonId, position) => {
  return await apiRequest(`/auth/team-order/${pokemonId}/move_to_position/`, {
    method: 'POST',
    body: { position },
  });
};

export const getLocations = async () => {
  return await apiRequest('/game/locations/');
};

export const travelToLocation = async (locationId) => {
  return await apiRequest('/auth/players/travel/', {
    method: 'POST',
    body: { location_id: locationId },
  });
};

export const getCurrentPlayer = async () => {
  return await apiRequest('/auth/players/');
};

export const healTeam = async () => {
  return await apiRequest('/auth/pokemon-center/heal_team/', {
    method: 'POST',
  });
};

export const getShopItems = async () => {
  return await apiRequest('/game/shop/');
};

export const buyItem = async (itemId) => {
  return await apiRequest(`/game/shop/${itemId}/buy/`, {
    method: 'POST',
  });
};

export const getTeamAndReserve = async () => {
  return await apiRequest('/auth/pokemon-center/get_team_and_reserve/');
};

export const moveToReserve = async (pokemonId) => {
  return await apiRequest(`/auth/pokemon-center/${pokemonId}/move-to-reserve/`, {
    method: 'POST',
  });
};

export const moveToTeam = async (pokemonId) => {
  return await apiRequest(`/auth/pokemon-center/${pokemonId}/move-to-team/`, {
    method: 'POST',
  });
};

export const getCurrentUser = async () => {
  return await apiRequest('/auth/users/me/');
};

export const getBag = async () => {
  return await apiRequest('/auth/bag/');
};

