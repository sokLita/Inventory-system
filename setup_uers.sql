-- Create users table if it doesn't exist
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Insert a test user (password will be 'admin123')
INSERT INTO users (email, password) VALUES 
('admin@example.com', 'pbkdf2:sha256:600000$dqcc5xw0mAhVzSGR$be6178f7a0a0fd360bcad2452e5a7a86d227adb6ee27f14df4a4375984a61142')
ON DUPLICATE KEY UPDATE id=id;