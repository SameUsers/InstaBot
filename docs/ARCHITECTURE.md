# Architecture Documentation

## Overview

InstaBot is built following a clean, layered architecture with clear separation of concerns. The application uses modern Python web development practices with FastAPI, SQLAlchemy, and AsyncIO for optimal performance.

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Client Layer                         │
│           (Web Interface / Mobile App / CLI)             │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                   API Layer (FastAPI)                    │
│  ┌──────────┬──────────┬──────────┬──────────┐         │
│  │  Auth    │  User    │  Post    │ Instagram│         │
│  │  Routes  │  Routes  │  Routes  │  Routes  │         │
│  └──────────┴──────────┴──────────┴──────────┘         │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│              Dependency Injection Layer                  │
│           (Authentication, Authorization)                │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│              Business Logic Layer                        │
│  ┌────────────┬────────────┬────────────┐              │
│  │   Token    │   Post     │ Instagram  │              │
│  │  Service   │ Publisher  │   Service  │              │
│  └────────────┴────────────┴────────────┘              │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│              Data Access Layer (Repository)              │
│  ┌────────────┬────────────┬────────────┐              │
│  │    User    │    Post    │ Instagram  │              │
│  │ Repository │ Repository │ Repository │              │
│  └────────────┴────────────┴────────────┘              │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│              Database Layer (SQLAlchemy)                 │
│            ┌──────────────────────────┐                 │
│            │     PostgreSQL 16        │                 │
│            └──────────────────────────┘                 │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│           External Services Layer                        │
│  ┌────────────┬────────────┬────────────┐              │
│  │ OpenRouter │   MinIO    │ Instagram  │              │
│  │     AI     │  Storage   │ Graph API  │              │
│  └────────────┴────────────┴────────────┘              │
└─────────────────────────────────────────────────────────┘
```

## Layer Descriptions

### 1. API Layer (`source/api/`)

**Purpose**: Handles HTTP requests/responses and routing.

**Responsibilities**:
- Request validation using Pydantic schemas
- Response serialization
- Error handling
- Rate limiting (future)
- API versioning

**Key Components**:
- `api/v1/auth.py` - Authentication endpoints
- `api/v1/user.py` - User management
- `api/v1/post.py` - Post CRUD operations
- `api/v1/instagram.py` - Instagram integration and webhooks
- `api/v1/post_context.py` - Post context management
- `api/v1/wiki_context.py` - Wiki context management

**Pattern**: RESTful API with OpenAPI 3.0 documentation

### 2. Dependency Injection (`source/dependencies/`)

**Purpose**: Provides shared dependencies across routes.

**Components**:
- `current_user.py` - JWT token validation and user extraction

**Pattern**: FastAPI Dependency Injection

### 3. Business Logic Layer (`source/services/`)

**Purpose**: Implements core business logic and orchestrates operations.

**Services**:
- **Token Service** (`auth/jwt.py`): JWT token generation and validation
- **Post Publisher** (`services/post_publisher.py`): Automated post publishing
- **Instagram Service** (`services/instagram.py`): Instagram API interactions
- **OpenRouter Service** (`services/openrouter.py`): AI content generation
- **Storage Service** (`services/storage.py`): MinIO file operations

**Pattern**: Service Layer with Stateless Operations

### 4. Data Access Layer (`source/repositories/`)

**Purpose**: Abstracts database operations using Repository pattern.

**Repositories**:
- `UserRepository` - User data access
- `PostRepository` - Post data access
- `InstagramRepository` - Instagram credentials management
- `PostContextRepository` - Post context CRUD
- `WikiContextRepository` - Wiki context CRUD

**Base Classes**:
- `BaseRepository` - Common CRUD operations
- `BaseContextRepository` - Generic context operations

**Pattern**: Repository Pattern with Generic Base Classes

### 5. Data Models (`source/models/`)

**Purpose**: Defines database schema and relationships.

**Models**:
- `User` - User accounts and authentication
- `Post` - Instagram post metadata
- `InstagramCredentials` - Instagram API tokens
- `PostBase` - Post generation context
- `Wikibase` - AI response context

**Pattern**: SQLAlchemy ORM with Declarative Base

### 6. Schemas (`source/schemas/`)

**Purpose**: Request/response validation and serialization.

**Components**:
- Pydantic models for all data structures
- Request schemas (validation)
- Response schemas (serialization)
- Internal schemas (DTOs)

**Pattern**: Schema-First API Design

## Design Patterns

### Repository Pattern

All database operations are abstracted through repositories, providing:
- Testability (easy to mock)
- Flexibility (switch DB implementations)
- Centralized query logic

```python
class UserRepository:
    @classmethod
    async def get_user_by_email(cls, email: str) -> UserSchema:
        # Centralized user lookup logic
        pass
```

### Dependency Injection

FastAPI's DI system is used for:
- Authentication token validation
- Database session management
- Service dependencies

```python
@router.get("/me")
async def get_current_user(
    user: CurrentUserSchema = Depends(current_user)
):
    # user is automatically validated and injected
    pass
```

### Service Layer

Business logic is encapsulated in services, keeping controllers thin:
- Single Responsibility Principle
- Reusable across different entry points
- Easier to test

### Factory Pattern

Used for creating HTTP clients and service instances with specific configurations.

## Data Flow

### Typical Request Flow

1. **Client** sends HTTP request to API endpoint
2. **API Layer** validates request using Pydantic schema
3. **Dependency Injection** validates JWT and extracts user
4. **API Layer** calls appropriate service method
5. **Service Layer** executes business logic
6. **Repository Layer** queries/updates database
7. **Response** flows back through layers
8. **Client** receives serialized JSON response

### Background Task Flow

1. **Scheduler** triggers post publishing task
2. **Post Publisher Service** queries pending posts
3. **For each post**: Instagram Service publishes via Graph API
4. **Repository** updates post status
5. **Logs** record success/failure

## Database Design

### Core Tables

- **user**: User accounts and authentication info
- **post**: Post metadata and scheduling
- **instagramcredentials**: API tokens per user
- **postbase**: Content generation context per user
- **wikibase**: AI response context per user

### Relationships

```
User (1) ────< (N) Post
User (1) ────< (1) InstagramCredentials
User (1) ────< (1) PostBase
User (1) ────< (1) Wikibase
```

## External Integrations

### Instagram Graph API

**Purpose**: Publish content and receive messages

**Endpoints Used**:
- `/messages` - Send messages
- `/media` - Create media containers
- `/media_publish` - Publish content

**Authentication**: Long-lived access tokens

### OpenRouter AI

**Purpose**: Generate text and images using AI models

**Models Used**:
- `google/gemini-2.5-flash` - Text generation
- `google/gemini-2.5-flash-image-preview` - Image generation

**Rate Limits**: Configured per API plan

### MinIO Object Storage

**Purpose**: Store and serve images

**Operations**:
- Upload generated images
- Generate public URLs
- Manage buckets

## Security Architecture

### Authentication Flow

1. User registers/logs in with email/password
2. Password hashed with bcrypt
3. JWT access + refresh tokens issued
4. Access token used for API calls
5. Refresh token used to obtain new access tokens

### Token Management

- **Access Token**: Short-lived (10 hours), stateless validation
- **Refresh Token**: Long-lived (30 days), validated against DB version
- **Token Versioning**: Allows token invalidation on logout/compromise

### Data Security

- Passwords never stored in plain text
- Sensitive fields encrypted/hashed
- HTTPS enforced in production
- CORS configured appropriately
- Input validation at all layers

## Scalability Considerations

### Horizontal Scaling

- Stateless API design (JWT-based auth)
- External database (PostgreSQL)
- External storage (MinIO)
- Background tasks can be offloaded to workers

### Performance Optimizations

- **Async I/O throughout**: FastAPI + SQLAlchemy async sessions
- **Non-blocking operations**: All I/O operations (MinIO, HTTP, DB) are async
- **Parallel processing**: Webhook messages and post publishing use concurrent execution
- **Thread pool for CPU-intensive tasks**: Bcrypt operations run in thread pool
- **Connection pooling**: Efficient database and HTTP connection management
- **Concurrency control**: Semaphores prevent resource exhaustion
- **Lazy initialization**: Resources initialized on-demand
- Caching layer (future Redis integration)
- Efficient database queries (indexes, pagination)

See [Async Optimization Documentation](ASYNC_OPTIMIZATION.md) for detailed information.

### Deployment Patterns

- Container orchestration (Docker Compose / Kubernetes)
- Load balancing for multiple instances
- Database replication for high availability
- CDN for static assets

## Testing Strategy

### Test Pyramid

1. **Unit Tests** (49 tests)
   - Individual functions/methods
   - Mocked dependencies
   - Fast execution

2. **Integration Tests** (0 currently)
   - Component interactions
   - Database integration
   - External service mocking

3. **API Tests** (12 tests)
   - End-to-end API flows
   - Real database
   - Service integration

### Test Coverage

Current coverage spans:
- Authentication logic
- Repository operations
- Service methods
- API endpoints
- Utility functions

## Monitoring & Observability

### Logging

- Structured logging with Loguru
- Contextual information (user_id, request_id)
- Log levels (DEBUG, INFO, WARNING, ERROR)
- Production-ready formatting

### Metrics (Future)

- Request rates and latencies
- Error rates by endpoint
- Database query performance
- Background task success/failure rates

### Health Checks

- `/` - Basic application health
- Dependency checks (DB, MinIO, external APIs)
- Graceful degradation

## Async Operations

InstaBot is fully optimized for asynchronous operations:

- ✅ All database operations use async SQLAlchemy sessions
- ✅ All HTTP requests use async clients (httpx)
- ✅ All file operations (MinIO) are non-blocking
- ✅ CPU-intensive tasks (bcrypt) run in thread pool
- ✅ Parallel processing for webhooks and post publishing
- ✅ Concurrency control with Semaphores

**Performance Benefits**:
- High throughput under concurrent load
- Non-blocking I/O operations
- Efficient resource utilization
- Scalable architecture

See [Async Optimization Documentation](ASYNC_OPTIMIZATION.md) for implementation details.

## Future Enhancements

### Planned Improvements

- [ ] Caching layer (Redis with aioredis)
- [ ] Message queue (Celery/RabbitMQ or async alternative)
- [ ] API rate limiting (async-aware)
- [ ] WebSocket support for real-time updates
- [ ] Streaming responses for large datasets
- [ ] Analytics and reporting
- [ ] Multi-tenant support
- [ ] Advanced scheduling options
- [ ] Content moderation

### Technical Debt

- Increase integration test coverage
- Implement comprehensive error recovery
- Add API versioning strategy
- Improve documentation for complex flows
- Optimize database queries further

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Instagram Graph API](https://developers.facebook.com/docs/instagram-api/)
- [OpenRouter Documentation](https://openrouter.ai/docs)

