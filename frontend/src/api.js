const API_BASE = '/api';

function getToken() {
  return localStorage.getItem('ocs_token');
}

async function request(url, options = {}) {
  const token = getToken();
  const headers = { 'Content-Type': 'application/json', ...options.headers };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${url}`, { ...options, headers });
  if (res.status === 204) return null;
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const err = new Error(body.detail || 'request_failed');
    err.status = res.status;
    throw err;
  }
  return res.json();
}

export const api = {
  register: (data) => request('/auth/register', { method: 'POST', body: JSON.stringify(data) }),
  login: (username, password) => {
    const form = new URLSearchParams();
    form.append('username', username);
    form.append('password', password);
    return fetch(`${API_BASE}/auth/login`, { method: 'POST', body: form }).then(async (res) => {
      if (!res.ok) throw new Error('invalid_credentials');
      return res.json();
    });
  },
  reauth: (password) => request('/auth/reauth', { method: 'POST', body: JSON.stringify({ password }) }),
  me: () => request('/auth/me'),
  updateMe: (data) => request('/auth/me', { method: 'PUT', body: JSON.stringify(data) }),

  getOrganizations: () => request('/organizations/'),
  createOrganization: (data) => request('/organizations/', { method: 'POST', body: JSON.stringify(data) }),
  getOrganization: (id) => request(`/organizations/${id}`),
  updateOrganization: (id, data) => request(`/organizations/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteOrganization: (id) => request(`/organizations/${id}`, { method: 'DELETE' }),

  getMembers: (orgId) => request(`/organizations/${orgId}/members/`),
  updateMember: (orgId, memberId, data) => request(`/organizations/${orgId}/members/${memberId}`, { method: 'PUT', body: JSON.stringify(data) }),
  removeMember: (orgId, memberId) => request(`/organizations/${orgId}/members/${memberId}`, { method: 'DELETE' }),

  getDepartments: (orgId) => request(`/organizations/${orgId}/departments/`),
  getDepartmentMembers: (orgId, deptId) => request(`/organizations/${orgId}/departments/${deptId}/members`),
  createDepartment: (orgId, data) => request(`/organizations/${orgId}/departments/`, { method: 'POST', body: JSON.stringify(data) }),
  updateDepartment: (orgId, deptId, data) => request(`/organizations/${orgId}/departments/${deptId}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteDepartment: (orgId, deptId) => request(`/organizations/${orgId}/departments/${deptId}`, { method: 'DELETE' }),

  getOrganizationLogs: (orgId, search = '') => request(`/organizations/${orgId}/logs?search=${encodeURIComponent(search)}`),

  getInvitations: (orgId) => request(`/organizations/${orgId}/invitations/`),
  createInvitation: (orgId, data) => request(`/organizations/${orgId}/invitations/`, { method: 'POST', body: JSON.stringify(data) }),
  cancelInvitation: (orgId, inviteId) => request(`/organizations/${orgId}/invitations/${inviteId}/cancel`, { method: 'POST' }),
  acceptInvitation: (orgId, token) => request(`/organizations/${orgId}/invitations/accept/${token}`, { method: 'POST' }),
  myPendingInvitations: () => request('/invitations/my-pending'),

  getChannels: (orgId) => request(`/organizations/${orgId}/chat/channels`),
  createChannel: (orgId, data) => request(`/organizations/${orgId}/chat/channels`, { method: 'POST', body: JSON.stringify(data) }),
  deleteChannel: (orgId, channelId) => request(`/organizations/${orgId}/chat/channels/${channelId}`, { method: 'DELETE' }),
  getMessages: (orgId, channelId) => request(`/organizations/${orgId}/chat/channels/${channelId}/messages`),
  sendMessage: (orgId, channelId, data) => request(`/organizations/${orgId}/chat/channels/${channelId}/messages`, { method: 'POST', body: JSON.stringify(data) }),
  deleteMessage: (orgId, messageId) => request(`/organizations/${orgId}/chat/messages/${messageId}`, { method: 'DELETE' }),

  getFinanceRecords: (orgId) => request(`/organizations/${orgId}/finance/`),
  createFinanceRecord: (orgId, data) => request(`/organizations/${orgId}/finance/`, { method: 'POST', body: JSON.stringify(data) }),
  approveFinanceRecord: (orgId, recordId, data) => request(`/organizations/${orgId}/finance/${recordId}/approve`, { method: 'PUT', body: JSON.stringify(data) }),

  getAbsences: (orgId) => request(`/organizations/${orgId}/absences/`),
  createAbsence: (orgId, data) => request(`/organizations/${orgId}/absences/`, { method: 'POST', body: JSON.stringify(data) }),
  approveAbsence: (orgId, absenceId, data) => request(`/organizations/${orgId}/absences/${absenceId}/approve`, { method: 'PUT', body: JSON.stringify(data) }),

  searchUsers: (q) => request(`/search/users?q=${encodeURIComponent(q)}`),

  // Boards (Kanban)
  getBoards: (orgId) => request(`/organizations/${orgId}/boards/`),
  createBoard: (orgId, data) => request(`/organizations/${orgId}/boards/`, { method: 'POST', body: JSON.stringify(data) }),
  getBoard: (orgId, boardId) => request(`/organizations/${orgId}/boards/${boardId}`),
  updateBoard: (orgId, boardId, data) => request(`/organizations/${orgId}/boards/${boardId}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteBoard: (orgId, boardId) => request(`/organizations/${orgId}/boards/${boardId}`, { method: 'DELETE' }),

  createColumn: (orgId, boardId, data) => request(`/organizations/${orgId}/boards/${boardId}/columns`, { method: 'POST', body: JSON.stringify(data) }),
  updateColumn: (orgId, boardId, colId, data) => request(`/organizations/${orgId}/boards/${boardId}/columns/${colId}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteColumn: (orgId, boardId, colId) => request(`/organizations/${orgId}/boards/${boardId}/columns/${colId}`, { method: 'DELETE' }),
  reorderColumns: (orgId, boardId, data) => request(`/organizations/${orgId}/boards/${boardId}/columns/reorder`, { method: 'PUT', body: JSON.stringify(data) }),

  createCard: (orgId, boardId, colId, data) => request(`/organizations/${orgId}/boards/${boardId}/cards?column_id=${colId}`, { method: 'POST', body: JSON.stringify(data) }),
  updateCard: (orgId, boardId, cardId, data) => request(`/organizations/${orgId}/boards/${boardId}/cards/${cardId}`, { method: 'PUT', body: JSON.stringify(data) }),
  moveCard: (orgId, boardId, cardId, data) => request(`/organizations/${orgId}/boards/${boardId}/cards/${cardId}/move`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteCard: (orgId, boardId, cardId) => request(`/organizations/${orgId}/boards/${boardId}/cards/${cardId}`, { method: 'DELETE' }),

  createLabel: (orgId, boardId, data) => request(`/organizations/${orgId}/boards/${boardId}/labels`, { method: 'POST', body: JSON.stringify(data) }),
  deleteLabel: (orgId, boardId, labelId) => request(`/organizations/${orgId}/boards/${boardId}/labels/${labelId}`, { method: 'DELETE' }),
  toggleCardLabel: (orgId, boardId, cardId, labelId, attach) => request(`/organizations/${orgId}/boards/${boardId}/cards/${cardId}/labels/${labelId}`, { method: attach ? 'POST' : 'DELETE' }),

  addCardComment: (orgId, boardId, cardId, data) => request(`/organizations/${orgId}/boards/${boardId}/cards/${cardId}/comments`, { method: 'POST', body: JSON.stringify(data) }),
  deleteCardComment: (orgId, boardId, cardId, commentId) => request(`/organizations/${orgId}/boards/${boardId}/cards/${cardId}/comments/${commentId}`, { method: 'DELETE' }),

  addChecklistItem: (orgId, boardId, cardId, data) => request(`/organizations/${orgId}/boards/${boardId}/cards/${cardId}/checklist`, { method: 'POST', body: JSON.stringify(data) }),
  updateChecklistItem: (orgId, boardId, cardId, itemId, data) => request(`/organizations/${orgId}/boards/${boardId}/cards/${cardId}/checklist/${itemId}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteChecklistItem: (orgId, boardId, cardId, itemId) => request(`/organizations/${orgId}/boards/${boardId}/cards/${cardId}/checklist/${itemId}`, { method: 'DELETE' }),

  adminGetUsers: (search) => request(`/admin/users?search=${encodeURIComponent(search || '')}`),
  adminUpdateUser: (userId, data) => request(`/admin/users/${userId}`, { method: 'PUT', body: JSON.stringify(data) }),
  adminDeactivateUser: (userId) => request(`/admin/users/${userId}`, { method: 'DELETE' }),
  adminGetOrganizations: () => request('/admin/organizations'),
  adminDeleteOrganization: (orgId) => request(`/admin/organizations/${orgId}`, { method: 'DELETE' }),
  adminGetAuditLog: () => request('/admin/audit-log'),
  adminGetOrgLogs: (orgId, search = '') => request(`/admin/organizations/${orgId}/logs?search=${encodeURIComponent(search)}`),
  adminGetStats: () => request('/admin/stats'),

  // Notifications
  getNotifications: (unreadOnly = false) => request(`/notifications/?unread_only=${unreadOnly ? 'true' : 'false'}`),
  markNotificationRead: (id) => request(`/notifications/${id}/read`, { method: 'POST' }),
  markAllNotificationsRead: () => request('/notifications/read-all', { method: 'POST' }),
};