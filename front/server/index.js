import express from 'express';
import cors from 'cors';
import apiRoutes from './routes/apiRoutes.js';

const app = express();
app.use(cors());
app.use(express.json());

// Main API Route wiring
app.use('/api', apiRoutes);

const PORT = 5000;
app.listen(PORT, () => {
  console.log(`Avalife backend API running on http://localhost:${PORT}`);
});
