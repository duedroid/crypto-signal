## develop
run docker
docker-compose -f docker-compose-local.yml up -d --build

create .env file

run server
docker exec api uvicorn main:app --reload --host 0.0.0.0 --port 8000

### custom boostrap theme css
- on path ```/app/static/bootstrap```
```
npm install 
```

- install extension
live sass compiller  
(https://marketplace.visualstudio.com/items?itemName=glenn2223.live-sass)[https://marketplace.visualstudio.com/items?itemName=glenn2223.live-sass]

- watch scss file ```/app/static/custom.scss```

- extension will generate file ```custom.min.css```, ```custom.min.css.map``` for use in project
- done