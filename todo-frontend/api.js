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

export const getTasks = () => request(BASE);
export const addTask = (task) =>
  request(BASE, { method: 'POST', body: JSON.stringify(task) });
export const updateTask = (id, fields) =>
  request(`${BASE}/${id}`, { method: 'PATCH', body: JSON.stringify(fields) });
export const deleteTask = (id) =>
  request(`${BASE}/${id}`, { method: 'DELETE' });