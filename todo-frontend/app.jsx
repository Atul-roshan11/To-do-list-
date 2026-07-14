import {useEffect, useState} from 'react';
import {getTasks, addTask, updateTask, deleteTask} from './src/api.js';
import './src/app.css';

export default function App() {
  const [tasks, setTasks] = useState([]);
  const [title, setTitle] = useState('');
  const [priority, setPriority] = useState('');
  const [deadline, setDeadline] = useState('');
  const [loggedIn, setLoggedIn] = useState(true);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [cursor, setCursor] = useState(null);
  const [hasMore, setHasMore] = useState(false);

  const loadTasks = (afterCursor = null) => {
    if (afterCursor) setLoadingMore(true);
    else setLoading(true);

    getTasks(afterCursor)
      .then((data) => {
        setTasks((prev) => (afterCursor ? [...prev, ...data.tasks] : data.tasks));
        setCursor(data.next_cursor);
        setHasMore(data.has_more);
        setLoggedIn(true);
      })
      .catch(() => setLoggedIn(false))
      .finally(() => {
        setLoading(false);
        setLoadingMore(false);
      });
  };

  useEffect(() => loadTasks(), []);
  const handleLoadMore = () => {
    if (cursor && !loadingMore) loadTasks(cursor);
  };

  const handleAdd = (e) => {
    e.preventDefault();
    if (!title.trim()) return;
    addTask({title, priority, deadline}).then((task) => {
      setTasks((prev) => [...prev, task]);
      setTitle('');
      setPriority('');
      setDeadline('');
    });
  };

  const handleToggle = (task) => {
    updateTask(task._id, { completed: !task.completed }).then((updated) => {
      setTasks((prev) => prev.map((t) => (t._id === updated._id ? updated : t)));
    });
  };

  const handleDelete = (id) => {
    deleteTask(id).then(() => {
      setTasks((prev) => prev.filter((t) => t._id !== id));
    });
  };

  if (loading) return <p className="center">Loading...</p>;

  if (!loggedIn) {
    return (
      <div className="center">
        <h1>To-Do List</h1>
        <p>Please log in to see your tasks.</p>
        <a className="login-btn" href="/login">Login with Google</a>
      </div>
    );
  }

  return (
    <div className="app">
      <div className="header">
        <h1>my tasks</h1>
        <a href="/logout">Logout</a>
      </div>

      <form onSubmit={handleAdd} className="task-form">
        <input
          placeholder="Task title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
        />
        <input
          placeholder="Priority"
          value={priority}
          onChange={(e) => setPriority(e.target.value)}
        />
        <input
          type="date"
          value={deadline}
          onChange={(e) => setDeadline(e.target.value)}
        />
        <button type="submit">Add</button>
      </form>

      <ul className="task-list">
        {tasks.map((task) => (
          <li key={task._id} className={task.completed ? 'done' : ''}>
            <label>
              <input
                type="checkbox"
                checked={task.completed}
                onChange={() => handleToggle(task)}
              />
              <span>{task.title}</span>
            </label>
            {task.priority && <span className="tag">{task.priority}</span>}
            {task.deadline && <span className="tag">{task.deadline}</span>}
            <button onClick={() => handleDelete(task._id)}>✕</button>
          </li>
        ))}
      </ul>

      {hasMore && (
        <button
          className="load-more"
          onClick={handleLoadMore}
          disabled={loadingMore}
        >
          {loadingMore ? 'Loading…' : 'Load more'}
        </button>
      )}
    </div>
  );
}

