-- Create users table if it doesn't exist
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert a test user (password is 'admin')
INSERT INTO users (username, password, email)
VALUES ('admin', 'admin', 'admin@example.com')
ON DUPLICATE KEY UPDATE username=username;