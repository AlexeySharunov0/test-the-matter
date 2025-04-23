# Mattermost Docker Deployment

This project provides a production-ready Docker deployment setup for [Mattermost](https://mattermost.com/), an open-source messaging platform. It includes Docker configurations for running Mattermost with a PostgreSQL database and a web proxy.

## Project Overview

- **Database:** PostgreSQL container for Mattermost data storage.
- **App:** Mattermost server container with persistent volumes for configuration, data, logs, and plugins.
- **Web:** Web proxy container exposing HTTP (80) and HTTPS (443) ports.

This setup is designed for easy deployment and management of Mattermost using Docker Compose.

## Installation

1. Clone this repository:

```bash
git clone <repository-url>
cd mattermost-docker
```

2. Ensure you have [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/) installed.

3. Configure environment variables if needed by editing the `docker-compose.yml` or setting them in your environment:

- `MM_USERNAME` - Mattermost database username (default: `mmuser`)
- `MM_PASSWORD` - Mattermost database password (default: `mmuser_password`)
- `MM_DBNAME` - Mattermost database name (default: `mattermost`)
- `DB_HOST` - Database host (default: `db`)
- `DB_PORT_NUMBER` - Database port (default: `5432`)
- `DB_USE_SSL` - SSL mode for database connection (default: `disable`)

4. Volumes are mounted under the `volumes/` directory for persistent data storage.

## Running the Project

Start the Mattermost stack using Docker Compose:

```bash
docker-compose up -d
```

This will start the database, app, and web proxy containers.

To stop the stack:

```bash
docker-compose down
```

## Configuration

- The Mattermost app container will generate a default configuration file if none exists.
- Configuration file is located at `/mattermost/config/config.json` inside the app container and mapped to `volumes/app/mattermost/config` on the host.
- You can customize the configuration by editing this file.

## Testing

Automated tests are located in the `tests/` directory. These tests cover authentication, channels, messages, and users.

To run tests, ensure you have the required Python environment and dependencies installed (see `requirements.txt`), then run:

```bash
pytest tests/
```

## Deployment Options

This project includes deployment manifests and instructions for various environments:

- **AWS Elastic Beanstalk:** See `contrib/aws/README.md`
- **Kubernetes:** See `contrib/kubernetes/README.md`
- **Docker Swarm:** See `contrib/swarm/` for stack files

## Contributing

Please see [CONTRIBUTING.md](mattermost-docker/CONTRIBUTING.md) for contribution guidelines.


For more information about Mattermost, visit the [official website](https://mattermost.com/) and [documentation](https://docs.mattermost.com/).
