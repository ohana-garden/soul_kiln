# FalkorDB for Railway deployment
FROM falkordb/falkordb:latest

# Railway uses $PORT, FalkorDB uses 6379 internally
EXPOSE 6379

# Persist data
VOLUME /data

# Start FalkorDB
CMD ["--loadmodule", "/usr/lib/redis/modules/falkordb.so", "--port", "6379"]
