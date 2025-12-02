import { apiRequest } from './api';

export const createRoom = async () => {
  return await apiRequest('/auth/pvp-battles/create_room/', {
    method: 'POST',
  });
};

export const getAvailableRooms = async () => {
  return await apiRequest('/auth/pvp-battles/available_rooms/');
};

export const joinRoom = async (roomCode) => {
  return await apiRequest('/auth/pvp-battles/join_room/', {
    method: 'POST',
    body: { room_code: roomCode },
  });
};

export const getBattleState = async (battleId) => {
  return await apiRequest(`/auth/pvp-battles/${battleId}/state/`);
};

export const pvpAttack = async (battleId, moveId) => {
  return await apiRequest(`/auth/pvp-battles/${battleId}/attack/`, {
    method: 'POST',
    body: { move_id: moveId },
  });
};

export const pvpSurrender = async (battleId) => {
  return await apiRequest(`/auth/pvp-battles/${battleId}/surrender/`, {
    method: 'POST',
  });
};

export const leaveRoom = async (roomCode) => {
  return await apiRequest('/auth/pvp-battles/leave_room/', {
    method: 'POST',
    body: { room_code: roomCode },
  });
};

export const getPvPStats = async () => {
  return await apiRequest('/auth/pvp-battles/stats/');
};

export const getBattleHistory = async () => {
  return await apiRequest('/auth/pvp-battles/history/');
};