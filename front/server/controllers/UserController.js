import UserModel from '../models/UserModel.js';

export const login = async (req, res) => {
    const { username, password } = req.body;
    try {
        const user = await UserModel.findByUsername(username);
        if (user && user.password === password) {
            const { password: _, ...userWithoutPw } = user;
            res.status(200).json(userWithoutPw);
        } else {
            res.status(401).json({ error: 'Invalid credentials' });
        }
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
};
