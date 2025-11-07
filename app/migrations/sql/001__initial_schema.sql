-- Initial schema for shared hosting API

CREATE TABLE IF NOT EXISTS auth_users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    username VARCHAR(100) NOT NULL UNIQUE,
    hashed_password TEXT NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(50),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    email_verified BOOLEAN NOT NULL DEFAULT FALSE,
    phone_verified BOOLEAN NOT NULL DEFAULT FALSE,
    isp_account_id VARCHAR(128),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_login TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS hosting_accounts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES auth_users (id) ON DELETE CASCADE,
    ftp_username VARCHAR(100) NOT NULL UNIQUE,
    ftp_password TEXT NOT NULL,
    home_directory TEXT NOT NULL,
    isp_ftp_id VARCHAR(128),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS domains (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES auth_users (id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL UNIQUE,
    status VARCHAR(32) NOT NULL DEFAULT 'pending',
    auto_renew BOOLEAN NOT NULL DEFAULT TRUE,
    expires_at DATE,
    registered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    isp_domain_id VARCHAR(128),
    nameservers TEXT[]
);

CREATE INDEX IF NOT EXISTS idx_domains_user_id ON domains (user_id);

CREATE TABLE IF NOT EXISTS dns_records (
    id SERIAL PRIMARY KEY,
    domain_id INTEGER NOT NULL REFERENCES domains (id) ON DELETE CASCADE,
    record_type VARCHAR(16) NOT NULL,
    name VARCHAR(255) NOT NULL,
    value TEXT NOT NULL,
    ttl INTEGER NOT NULL DEFAULT 3600,
    priority INTEGER,
    isp_record_id VARCHAR(128),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_dns_records_domain_id ON dns_records (domain_id);

CREATE TABLE IF NOT EXISTS hosting_sites (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES auth_users (id) ON DELETE CASCADE,
    domain_id INTEGER REFERENCES domains (id) ON DELETE SET NULL,
    root_path TEXT NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'active',
    isp_site_id VARCHAR(128),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_hosting_sites_user_id ON hosting_sites (user_id);


