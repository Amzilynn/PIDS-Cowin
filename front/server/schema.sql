CREATE DATABASE IF NOT EXISTS avalife_db;
USE avalife_db;

CREATE TABLE IF NOT EXISTS regions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    perf INT NOT NULL,
    reps INT NOT NULL,
    strategy TEXT NOT NULL,
    lat DECIMAL(10, 8),
    lng DECIMAL(11, 8)
);

CREATE TABLE IF NOT EXISTS stats (
    id INT AUTO_INCREMENT PRIMARY KEY,
    label VARCHAR(100) NOT NULL,
    value VARCHAR(50) NOT NULL,
    trend VARCHAR(50),
    sector ENUM('Medical', 'Commercial') NOT NULL DEFAULT 'Medical'
);

CREATE TABLE IF NOT EXISTS stream_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    message VARCHAR(255) NOT NULL,
    type ENUM('SCAN', 'AI', 'DATA') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Initial Mock Data

INSERT IGNORE INTO regions (name, perf, reps, strategy, lat, lng) VALUES 
('Tunis', 94, 42, 'Saturation reached. Pivot to private clinics.', 36.8065, 10.1815),
('Sfax', 68, 18, 'High retail volume. Increase visit freq by 20%.', 34.7400, 10.7600);

('Active Units', '112', '+4');

INSERT IGNORE INTO stream_logs (message, type) VALUES 
('> [SCAN] Regional discrepancies in Sfax detected', 'SCAN'),
('> [AI] Recommend shift to cardio-hub', 'AI'),
('> [DATA] Waiting for Tunis sync...', 'DATA');

CREATE TABLE IF NOT EXISTS physician_visits (
    id INT AUTO_INCREMENT PRIMARY KEY,
    doctor_name VARCHAR(100) NOT NULL,
    specialty VARCHAR(100) NOT NULL,
    hospital VARCHAR(150),
    status ENUM('Completed', 'Pending', 'Cancelled') NOT NULL,
    scheduled_time TIME NOT NULL
);

CREATE TABLE IF NOT EXISTS rep_kpis (
    id INT AUTO_INCREMENT PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL,
    current_value INT NOT NULL,
    target_value INT NOT NULL,
    unit VARCHAR(50) NOT NULL
);

INSERT IGNORE INTO physician_visits (doctor_name, specialty, hospital, status, scheduled_time) VALUES 
('Dr. Amine Ben Ali', 'Cardiologist', 'Clinique Pasteur', 'Completed', '09:00:00'),
('Dr. Salma Trabelsi', 'Endocrinologist', 'Polyclinique El Menzah', 'Completed', '11:30:00'),
('Dr. Youssef Gharbi', 'General Practice', 'Centre Medical', 'Pending', '14:00:00'),
('Dr. Hiba Mansouri', 'Internal Medicine', 'Hopital Charles Nicolle', 'Pending', '16:15:00');

INSERT IGNORE INTO rep_kpis (metric_name, current_value, target_value, unit) VALUES 
('Daily Call Rate', 4, 8, 'Visits'),
('Sample Distribution', 45, 100, 'Units'),
('Prescription ROI', 82, 100, '%');

CREATE TABLE IF NOT EXISTS simulation_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    role ENUM('doctor', 'delegate') NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS medical_products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_name VARCHAR(100) NOT NULL,
    category VARCHAR(100),
    market_share_pct INT,
    growth_pct INT,
    prescriptions_this_month INT,
    sector ENUM('Medical', 'Commercial') NOT NULL DEFAULT 'Medical'
);

INSERT IGNORE INTO simulation_sessions (role, message) VALUES
('doctor', 'Dr. Khalil (AI Evaluator): Welcome delegate. Let us begin with pharmacology. What is the primary mechanism of action of Avalife Core?'),
('delegate', 'Avalife Core is an SGLT2 inhibitor that works by blocking glucose reabsorption in the renal proximal tubule, leading to glucosuria and blood pressure reduction.');

-- Categorize products
INSERT IGNORE INTO medical_products (product_name, category, market_share_pct, growth_pct, prescriptions_this_month, sector) VALUES
('Avalive Core', 'SGLT2 (Cardio)', 64, 12, 1420, 'Medical'),
('Avalive Plus', 'Endo Combo', 22, 8, 510, 'Medical'),
('Avalive Lite', 'T2D Base', 10, 3, 230, 'Medical'),
('Avalive Pro', 'Commercial Premium', 85, 20, 2900, 'Commercial');

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    password VARCHAR(255) NOT NULL,
    role ENUM('admin', 'delegate', 'doctor') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS evaluation_reports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    eye_score INT DEFAULT 0,
    know_score INT DEFAULT 0,
    clarity_score INT DEFAULT 0,
    objection_score INT DEFAULT 0,
    feedback TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Update simulation_sessions to track which delegate sent the message
ALTER TABLE simulation_sessions ADD COLUMN IF NOT EXISTS user_id INT;

-- Initial User Data
INSERT IGNORE INTO users (username, name, password, role) VALUES 
('admin', 'Admin User', 'admin123', 'admin'),
('samar', 'Samar Ben Ali', 'samar123', 'delegate'),
('youssef', 'Youssef Gharbi', 'youssef123', 'delegate');
