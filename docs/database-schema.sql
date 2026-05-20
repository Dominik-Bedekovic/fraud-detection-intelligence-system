CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description VARCHAR(255)
);

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role_id INTEGER NOT NULL REFERENCES roles(id),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_email_verified BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    step INTEGER NOT NULL DEFAULT 1,
    type VARCHAR(50) NOT NULL,
    amount DOUBLE PRECISION NOT NULL,
    oldbalanceOrg DOUBLE PRECISION NOT NULL,
    newbalanceOrig DOUBLE PRECISION NOT NULL,
    oldbalanceDest DOUBLE PRECISION NOT NULL,
    newbalanceDest DOUBLE PRECISION NOT NULL,
    source VARCHAR(20) NOT NULL DEFAULT 'single',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE prediction_results (
    id SERIAL PRIMARY KEY,
    transaction_id INTEGER NOT NULL REFERENCES transactions(id),
    prediction INTEGER NOT NULL,
    label VARCHAR(50) NOT NULL,
    probability DOUBLE PRECISION NOT NULL,
    model_name VARCHAR(100),
    model_version VARCHAR(100),
    threshold DOUBLE PRECISION,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE email_verification_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    used_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO roles (name, description)
VALUES
    ('user', 'Default registered application user'),
    ('admin', 'Administrator with full access'),
    ('analyst', 'User allowed to review fraud prediction results');