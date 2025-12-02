import { apiRequest } from './api';
import { setToken, setUser, removeToken, removeUser } from '../utils/auth';

export const login = async (username, password) => {
  const data = await apiRequest('/auth/users/login/', {
    method: 'POST',
    body: { username, password },
  });
  
  if (data.token && data.user) {
    setToken(data.token);
    setUser(data.user);
  }
  return data;
};

export const register = async (username, email, password) => {
  const data = await apiRequest('/auth/users/register/', {
    method: 'POST',
    body: { username, email, password },
  });
  return data;
};

export const getCurrentUser = async () => {
  return await apiRequest('/auth/users/me/');
};

export const chooseStarter = async (starterId) => {
  return await apiRequest('/auth/players/choose_starter/', {
    method: 'POST',
    body: { starter_id: starterId },
  });
};

export const logout = () => {
  removeToken();
  removeUser();
};