import { apiRequest } from './api';

export const startWildBattle = async () => {
  return await apiRequest('/auth/battles/start_wild_battle/', {
    method: 'POST',
  });
};
export const startTrainerBattle = async () => {
  return await apiRequest('/auth/battles/start_trainer_battle/', {
    method: 'POST',
  });
};

export const attackPokemon = async (battleId, moveId) => {
  return await apiRequest(`/auth/battles/${battleId}/attack/`, {
    method: 'POST',
    body: { move_id: moveId },
  });
};

export const battleUseItem = async (battleId, itemType) => {
  return await apiRequest(`/auth/battles/${battleId}/use_item/`, {
    method: 'POST',
    body: { item_type: itemType },
  });
};

export const switchPokemon = async (battleId, pokemonId) => {
  return await apiRequest(`/auth/battles/${battleId}/switch_pokemon/`, {
    method: 'POST',
    body: { pokemon_id: pokemonId },
  });
};

export const fleeBattle = async (battleId) => {
  return await apiRequest(`/auth/battles/${battleId}/flee/`, {
    method: 'POST',
  });
};

export const getBattleDetails = async (battleId) => {
  return await apiRequest(`/auth/battles/${battleId}/`);
};