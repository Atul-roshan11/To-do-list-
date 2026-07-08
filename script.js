let tasks = [];

async function loadTasks() {
  const res = await fetch('/api/todo');
  tasks = await res.json();
  renderTasks();
}

function renderTasks() {
  const list = document.getElementById('taskList');
  list.innerHTML = '';
  tasks.forEach(task => {
    const li = document.createElement('li');
    li.innerHTML = `
      <input type="checkbox" ${task.completed ? 'checked' : ''} data-id="${task._id}">
      <span style="text-decoration:${task.completed ? 'line-through' : 'none'}">
        ${task.title} [${task.priority}] — due ${task.deadline}
      </span>
      <button data-delete="${task._id}">Delete</button>
    `;
    list.appendChild(li);
  });
}

document.getElementById('addBtn').addEventListener('click', async () => {
  const title = document.getElementById('taskInput').value;
  const priority = document.getElementById('priorityInput').value;
  const deadline = document.getElementById('deadlineInput').value;
  if (!title) return;

  const res = await fetch('/api/todo', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, priority, deadline })
  });
  const newTask = await res.json();
  tasks.push(newTask);
  renderTasks();

  document.getElementById('taskInput').value = '';
});

document.getElementById('taskList').addEventListener('click', async (e) => {
  if (e.target.matches('input[type=checkbox]')) {
    const id = e.target.dataset.id;
    const task = tasks.find(t => t._id === id);
    const updated = !task.completed;

    await fetch(`/api/todo/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ completed: updated })
    });

    task.completed = updated;
    renderTasks();
  }

  if (e.target.matches('button[data-delete]')) {
    const id = e.target.dataset.delete;

    await fetch(`/api/todo/${id}`, { method: 'DELETE' });

    tasks = tasks.filter(t => t._id !== id);
    renderTasks();
  }
});

loadTasks();
