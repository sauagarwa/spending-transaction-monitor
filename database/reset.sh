#!/bin/bash

        
# Drop all tables
podman-compose down -v && podman rm spending-monitor-db

podman-compose --file compose.yaml up --detach   

#npm run db:reset

npm run db:generate

npm run db:migrate

npm run db:studio




