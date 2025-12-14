# FalkorDB-Specific Features and Differences

FalkorDB is a high-performance graph database that implements the Cypher query language. This document covers FalkorDB-specific behaviors and differences from Neo4j.

## Overview

FalkorDB (formerly RedisGraph) is:
- Built on Redis as storage backend
- Optimized for low latency and high throughput
- Uses sparse matrix representation for graphs
- Implements openCypher with some variations

## Supported Cypher Features

### Fully Supported

- MATCH, OPTIONAL MATCH
- WHERE with all standard predicates
- RETURN, WITH, UNWIND
- CREATE, MERGE, SET, DELETE, REMOVE
- ORDER BY, SKIP, LIMIT
- UNION, UNION ALL
- Aggregation functions (count, sum, avg, min, max, collect)
- String functions
- List functions
- Mathematical functions
- Path functions

### Partially Supported or Different

#### Variable-Length Paths

```cypher
-- Supported
MATCH (a)-[*1..5]->(b) RETURN a, b

-- Supported but be careful with performance
MATCH (a)-[*]->(b) RETURN a, b

-- shortestPath is supported
MATCH path = shortestPath((a)-[*..10]->(b)) RETURN path

-- allShortestPaths is supported
MATCH paths = allShortestPaths((a)-[*..10]->(b)) RETURN paths
```

#### Subqueries

```cypher
-- CALL {} subqueries: Check version support
-- Some versions may not support all subquery patterns
CALL {
    MATCH (n:Person) RETURN n LIMIT 10
}
RETURN n.name
```

#### List Comprehensions

```cypher
-- Fully supported
RETURN [x IN range(1,10) WHERE x % 2 = 0 | x * 2] AS evensDoubled

-- Pattern comprehensions supported
MATCH (p:Person)
RETURN p.name, [(p)-[:KNOWS]->(f) | f.name] AS friendNames
```

### Not Supported (as of recent versions)

- `FOREACH` clause (use UNWIND + CREATE instead)
- `LOAD CSV` (use application-level loading)
- `CALL ... YIELD` for external procedures (no stored procedures)
- `CREATE CONSTRAINT` (schema constraints)
- Full-text indexes (use Redis Search module separately)
- Point/spatial types
- Temporal types (use Unix timestamps instead)

## Data Types

### Supported Types

| Type | Example | Notes |
|------|---------|-------|
| Integer | `42` | 64-bit signed |
| Float | `3.14` | IEEE 754 double |
| String | `'hello'` | UTF-8 |
| Boolean | `true`, `false` | |
| Null | `null` | |
| List | `[1, 2, 3]` | Homogeneous preferred |
| Map | `{key: 'value'}` | |
| Node | `(n)` | Internal representation |
| Relationship | `[r]` | Internal representation |
| Path | `path = (a)-[]->(b)` | |

### Type Differences from Neo4j

```cypher
-- No native date/datetime
-- Instead of: date('2024-01-15')
-- Use: Unix timestamp
SET n.created = 1705276800

-- No duration type
-- Instead of: duration('P30D')
-- Use: Seconds or compute manually
SET n.expiresAt = n.created + (30 * 24 * 60 * 60)

-- No point/spatial
-- Store as separate lat/lon properties
SET n.lat = 40.7128, n.lon = -74.0060
```

## Indexes

### Creating Indexes

```cypher
-- Create index on single property
CREATE INDEX ON :Person(email)

-- Index is created asynchronously
-- Query returns immediately, index builds in background
```

### Index Behavior

- Indexes are used automatically by the query planner
- No composite indexes (single property only)
- No unique constraints (enforce at application level)
- Index on ID is automatic and implicit

### Checking Indexes

```cypher
-- List all indexes
CALL db.indexes()

-- Index info returned as result set
```

## Query Optimization

### FalkorDB Query Planner

FalkorDB uses a cost-based optimizer that:
- Estimates cardinality based on stored statistics
- Chooses index usage when beneficial
- Plans traversal order to minimize intermediate results

### Performance Characteristics

**Fast operations:**
- Index lookups: O(log n)
- Relationship traversal: O(degree)
- Label filtering during scan: Efficient

**Potentially slow operations:**
- Full graph scans without label filter
- Very long variable-length paths
- Large aggregations
- Cartesian products

### Using EXPLAIN

```cypher
EXPLAIN MATCH (n:Person) WHERE n.email = $email RETURN n
```

Output shows:
- Operation tree
- Estimated cardinality
- Index usage

### Memory Considerations

FalkorDB stores graphs in memory:
- Ensure sufficient RAM for your graph size
- Large result sets consume memory
- Use LIMIT to control result size
- Consider pagination for large traversals

## Connection and Configuration

### Connection Parameters

```python
from falkordb import FalkorDB

# Default connection
db = FalkorDB(host='localhost', port=6379)

# With authentication
db = FalkorDB(host='localhost', port=6379, password='your-password')

# Select graph
graph = db.select_graph('my_graph')
```

### Executing Queries

```python
# Read query
result = graph.query("MATCH (n:Person) RETURN n.name LIMIT 10")

# With parameters (RECOMMENDED)
result = graph.query(
    "MATCH (n:Person) WHERE n.email = $email RETURN n",
    {'email': 'alice@example.com'}
)

# Access results
for row in result.result_set:
    print(row[0])  # First column

# Get headers
print(result.header)
```

### Transaction Behavior

- Each query is atomic
- No multi-statement transactions in open source version
- FalkorDB Enterprise supports multi-statement transactions

## Best Practices for FalkorDB

### 1. Always Use Parameters

```cypher
-- Good
MATCH (n:Person) WHERE n.email = $email RETURN n

-- Bad (injection risk, no query caching)
MATCH (n:Person) WHERE n.email = 'alice@example.com' RETURN n
```

### 2. Create Indexes for Lookup Properties

```cypher
CREATE INDEX ON :Person(email)
CREATE INDEX ON :Product(sku)
CREATE INDEX ON :Order(orderId)
```

### 3. Use Labels for All Nodes

```cypher
-- Good: Labeled nodes enable efficient filtering
CREATE (n:Person {name: 'Alice'})

-- Bad: Unlabeled nodes require full scan
CREATE (n {name: 'Alice'})
```

### 4. Bound Variable-Length Paths

```cypher
-- Good
MATCH (a)-[*1..5]->(b) RETURN a, b

-- Risky
MATCH (a)-[*]->(b) RETURN a, b
```

### 5. Return Only Needed Properties

```cypher
-- Good: Return specific properties
MATCH (n:Person) RETURN n.name, n.email

-- Less efficient: Return entire node
MATCH (n:Person) RETURN n
```

### 6. Batch Large Operations

```python
# Instead of one large query
# Break into batches
batch_size = 1000
offset = 0

while True:
    result = graph.query(f"""
        MATCH (n:OldLabel)
        WITH n LIMIT {batch_size}
        SET n:NewLabel
        REMOVE n:OldLabel
        RETURN count(n) as updated
    """)

    updated = result.result_set[0][0]
    if updated == 0:
        break
    offset += batch_size
```

## Differences Summary Table

| Feature | Neo4j | FalkorDB |
|---------|-------|----------|
| Temporal types | Native date/datetime | Use timestamps |
| Spatial types | Point | Not supported |
| Constraints | UNIQUE, EXISTS | Not supported |
| Full-text search | Built-in | Use Redis Search |
| Stored procedures | APOC, custom | Not supported |
| Transactions | Multi-statement | Single query (OSS) |
| Composite indexes | Yes | No |
| FOREACH | Yes | No (use UNWIND) |
| LOAD CSV | Yes | No (use app) |

## Version Compatibility

Check your FalkorDB version for specific feature support:

```cypher
-- Get server info
CALL dbms.info()
```

Different versions may have varying levels of Cypher support. Always test queries against your specific FalkorDB version.
