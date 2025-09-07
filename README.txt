docker network create grx
docker compose --profile full build --no-cache && docker compose --profile full up -d


Invoke-RestMethod -Uri 'http://host.docker.internal:8000/rest/v1/' `
  -Headers @{ 'apikey' = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpseWhpbGxwZGRtZm15b2t3eGdzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0MTU4MzM0NywiZXhwIjoyMDU3MTU5MzQ3fQ.jBZVwwPKBAXWQuUDb2knnKc5hoPqRe9J-W-pIV0dWb8'; 'Authorization' = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpseWhpbGxwZGRtZm15b2t3eGdzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0MTU4MzM0NywiZXhwIjoyMDU3MTU5MzQ3fQ.jBZVwwPKBAXWQuUDb2knnKc5hoPqRe9J-W-pIV0dWb8" } `
  -Method Get -Verbose
