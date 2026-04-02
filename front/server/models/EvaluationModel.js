import { pool } from '../db.js';

class EvaluationModel {
    static async getByUserId(userId) {
        const [rows] = await pool.query('SELECT * FROM evaluation_reports WHERE user_id = ? ORDER BY created_at DESC', [userId]);
        return rows;
    }

    static async create(userId, scores) {
        const { eye, know, clarity, objection, feedback } = scores;
        const [result] = await pool.query(
            'INSERT INTO evaluation_reports (user_id, eye_score, know_score, clarity_score, objection_score, feedback) VALUES (?, ?, ?, ?, ?, ?)',
            [userId, eye, know, clarity, objection, feedback]
        );
        return result.insertId;
    }
}

export default EvaluationModel;
