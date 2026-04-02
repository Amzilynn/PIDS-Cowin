import { VisitModel } from '../models/VisitModel.js';

export const getVisits = async (req, res) => {
  try {
    const data = await VisitModel.getAll();
    res.json(data);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};
