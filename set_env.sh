#!/# Common
# *Set Environment Variables For Local Development Only*
# command to run: source set_env.sh

# Core Settings
export ALLOWED_HOSTS="*"
export CORS_ORIGINS="*"

# DB config
export POSTGRES_HOST='localhost'
export POSTGRES_PORT='5432'
export POSTGRES_USER='postgres'
export POSTGRES_PASSWORD=''
export POSTGRES_NAME='ai_code_editor'
export POSTGRES_POOL_SIZE='5'
export POSTGRES_MAX_OVERFLOW='10'

# Redis Config
export REDIS_HOST='localhost'
export REDIS_PORT='6379'
export REDIS_PASSWORD=''
export REDIS_DB='0'
export REDIS_MAX_CONNECTIONS='10'
export REDIS_CONNECTION_TIMEOUT='5'
export REDIS_HEALTH_CHECK_INTERVAL='30'

# Rate Limit Config
export READ_RATE_LIMITING_PER_MIN='60'
export WRITE_RATE_LIMITING_PER_MIN='30'

# JWT Config
export  JWT_SECRET_KEY="test" # only for development
export  JWT_ALGORITHM="HS256"
export  JWT_ACCESS_TOKEN_EXPIRE_MINUTES='1800'

# OpenAI Config
export OPENAI_API_KEY=''
export OPENAI_API_MODEL=''