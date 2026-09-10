import apiClient from './api';

export const notificationService = {
  getNotifications: async (unreadOnly = false) => {
    const response = await apiClient.get('/notifications', {
      params: { unread_only: unreadOnly },
    });
    return response.data;
  },

  markAsRead: async (id) => {
    const response = await apiClient.put(`/notifications/${id}/read`);
    return response.data;
  },

  markAllRead: async () => {
    const response = await apiClient.put('/notifications/read-all');
    return response.data;
  },

  getUnreadCount: async () => {
    const response = await apiClient.get('/notifications/unread-count');
    return response.data;
  },
};

export default notificationService;
