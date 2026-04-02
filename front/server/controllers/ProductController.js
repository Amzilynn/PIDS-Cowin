import { ProductModel } from '../models/ProductModel.js';

export const getProducts = async (req, res) => {
  try {
    const data = await ProductModel.getAll();
    res.json(data);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};
