#!/# Common
# *Set Environment Variables For Local Development Only*
# command to run: source set_env.sh

# Core Settings
export ALLOWED_HOSTS="127.0.0.1,localhost"

# DB config
export POSTGRES_HOST='localhost'
export POSTGRES_PORT='5432'
export POSTGRES_USER='postgres'
export POSTGRES_PASSWORD=''
export POSTGRES_NAME='ai_code_editor'
export POSTGRES_POOL_SIZE='5'
export POSTGRES_MAX_OVERFLOW='10'

# JWT Config
export  JWT_SECRET_KEY="b5df46aafffd8a6cf78b9022ca91ec46d1534e9c7339c653553450a60884d1cd" # only for development
export  JWT_ALGORITHM="HS256"
export  JWT_ACCESS_TOKEN_EXPIRE_MINUTES='30'

# OpenAI Config
export OPEN_AI_KEY=''
export OPEN_AI_MODEL=''