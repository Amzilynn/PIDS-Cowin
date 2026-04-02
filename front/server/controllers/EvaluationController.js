import EvaluationModel from '../models/EvaluationModel.js';

export const getUserReports = async (req, res) => {
    const { userId } = req.params;
    try {
        const reports = await EvaluationModel.getByUserId(userId);
        res.status(200).json(reports);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
};

export const saveReport = async (req, res) => {
    const { userId, scores } = req.body;
    try {
        const id = await EvaluationModel.create(userId, scores);
        res.status(201).json({ id });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
};
