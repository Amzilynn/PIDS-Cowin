import { pool } from '../db.js';

export const SimulationModel = {
  getHistory: async () => {
    const [rows] = await pool.query('SELECT * FROM simulation_sessions ORDER BY created_at ASC');
    return rows;
  },
  addMessage: async (role, message) => {
    await pool.query('INSERT INTO simulation_sessions (role, message) VALUES (?, ?)', [role, message]);
  },
  getContext: async () => {
    const [rows] = await pool.query('SELECT topic FROM user_context ORDER BY frequency DESC LIMIT 5');
    return rows.map(r => r.topic);
  },
  addTopic: async (topic) => {
    await pool.query(
      'INSERT INTO user_context (user_id, topic, frequency) VALUES (1, ?, 1) ON DUPLICATE KEY UPDATE frequency = frequency + 1',
      [topic]
    );
  }
};
