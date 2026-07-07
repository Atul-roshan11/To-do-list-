let tasks = [];

function renderTasks() {
  const list = document.getElementById('taskList');
  list.innerHTML = '';
  tasks.forEach(task => {
    const li = document.createElement('li');
    li.innerHTML = `
      <input type="checkbox" ${task.completed ? 'checked' : ''} data-id="${task.id}">
      <span style="text-decoration:${task.completed ? 'line-through' : 'none'}">
        ${task.title} [${task.priority}] — due ${task.deadline}
      </span>
      <button data-delete="${task.id}">Delete</button>
    `;
    list.appendChild(li);
  });
}

document.getElementById('addBtn').addEventListener('click', () => {
  const title = document.getElementById('taskInput').value;
  const priority = document.getElementById('priorityInput').value;
  const deadline = document.getElementById('deadlineInput').value;
  if (!title) return;

  tasks.push({
    id: Date.now(),
    title, priority, deadline,
    completed: false
  });
  renderTasks();
});

document.getElementById('taskList').addEventListener('click', (e) => {
  if (e.target.matches('input[type=checkbox]')) {
    const id = Number(e.target.dataset.id);
    const task = tasks.find(t => t.id === id);
    task.completed = !task.completed;
    renderTasks();
  }
  if (e.target.matches('button[data-delete]')) {
    const id = Number(e.target.dataset.delete);
    tasks = tasks.filter(t => t.id !== id);
    renderTasks();
  }
});