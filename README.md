## develop
run docker
docker-compose -f docker-compose-local.yml up -d --build

create .env file

run server
docker exec api uvicorn main:app --reload --host 0.0.0.0 --port 8000