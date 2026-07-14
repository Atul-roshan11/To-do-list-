const BASE = '/api/todo';

async function request(url, options = {}) {
  const res = await fetch(url, {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  const contentType = res.headers.get('content-type') || '';
  if (!res.ok || !contentType.includes('application/json')) {
    throw new Error('unauthenticated');
  }
  return res.json();
}

// Now accepts a cursor + limit so the caller can page through results.
// Expects the backend to respond with { tasks, next_cursor, has_more }
// (see the backend note in chat — /api/todo currently returns a bare array).
export const getTasks = (cursor, limit = 10) => {
  const params = new URLSearchParams({ limit });
  if (cursor) params.set('cursor', cursor);
  return request(`${BASE}?${params.toString()}`);
};

export const addTask = (task) =>
  request(BASE, { method: 'POST', body: JSON.stringify(task) });
export const updateTask = (id, fields) =>
  request(`${BASE}/${id}`, { method: 'PATCH', body: JSON.stringify(fields) });
export const deleteTask = (id) =>
  request(`${BASE}/${id}`, { method: 'DELETE' });