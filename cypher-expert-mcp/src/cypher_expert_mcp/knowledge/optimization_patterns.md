# Cypher Query Optimization Patterns

A guide to writing efficient Cypher queries and recognizing performance anti-patterns.

## Reading Query Plans

### Using EXPLAIN and PROFILE

```cypher
-- EXPLAIN: Show plan without executing
EXPLAIN MATCH (n:Person) WHERE n.email = $email RETURN n

-- PROFILE: Execute and show actual statistics
PROFILE MATCH (n:Person) WHERE n.email = $email RETURN n
```

### Key Metrics

| Metric | Description | What to Look For |
|--------|-------------|------------------|
| Estimated Rows | Planner's row estimate | Large numbers indicate potential issues |
| Actual Rows | Real rows processed | Compare to estimated for accuracy |
| DB Hits | Database operations | Lower is better |
| Memory | Memory used | Watch for large sorts/aggregations |

### Warning Signs in Query Plans

1. **AllNodesScan** - Scanning every node in the database
2. **NodeByLabelScan** - Scanning all nodes with a label (no index)
3. **Eager** - Materializing results in memory
4. **CartesianProduct** - Unconnected patterns multiplying results

## Index Optimization

### When to Create Indexes

```cypher
-- Create index for frequently queried property
CREATE INDEX FOR (n:Person) ON (n.email)

-- Composite index for multi-property queries
CREATE INDEX FOR (n:Person) ON (n.lastName, n.firstName)

-- Full-text index for text search
CREATE FULLTEXT INDEX personNames FOR (n:Person) ON EACH [n.name]
```

### Index Usage Patterns

**Good: Index will be used**
```cypher
-- Equality on indexed property
MATCH (n:Person) WHERE n.email = $email RETURN n

-- STARTS WITH on indexed string
MATCH (n:Person) WHERE n.name STARTS WITH $prefix RETURN n

-- Range on indexed property
MATCH (n:Person) WHERE n.age > 30 RETURN n
```

**Bad: Index cannot be used**
```cypher
-- Function on property
MATCH (n:Person) WHERE toLower(n.email) = $email RETURN n
-- Fix: Store normalized version

-- ENDS WITH or CONTAINS
MATCH (n:Person) WHERE n.name ENDS WITH $suffix RETURN n
-- Fix: Use full-text index

-- OR conditions across different properties
MATCH (n:Person) WHERE n.email = $email OR n.phone = $phone RETURN n
-- Fix: Use UNION
```

### Forcing Index Usage

```cypher
-- When optimizer doesn't pick the right index
MATCH (n:Person)
USING INDEX n:Person(email)
WHERE n.email = $email
RETURN n
```

## Cardinality Management

### Use WITH to Reduce Intermediate Results

```cypher
-- Bad: Large intermediate result
MATCH (a:Person)-[:KNOWS]-(b:Person)-[:KNOWS]-(c:Person)
WHERE a.name = $name
RETURN c.name

-- Good: Checkpoint with WITH
MATCH (a:Person)-[:KNOWS]-(b:Person)
WHERE a.name = $name
WITH DISTINCT b
MATCH (b)-[:KNOWS]-(c:Person)
RETURN DISTINCT c.name
```

### Early Filtering

```cypher
-- Bad: Filter late
MATCH (p:Person)-[:PURCHASED]->(prod:Product)
RETURN p.name, prod.name
WHERE p.country = $country

-- Good: Filter early
MATCH (p:Person)
WHERE p.country = $country
MATCH (p)-[:PURCHASED]->(prod:Product)
RETURN p.name, prod.name
```

### LIMIT Early When Possible

```cypher
-- Bad: Sort everything then limit
MATCH (p:Person)
WITH p
ORDER BY p.created DESC
RETURN p.name
LIMIT 10

-- Good: Subquery with early limit (Neo4j 4.0+)
CALL {
    MATCH (p:Person)
    RETURN p
    ORDER BY p.created DESC
    LIMIT 10
}
RETURN p.name
```

## Anti-Pattern Fixes

### Cartesian Products

```cypher
-- Bad: Disconnected patterns create Cartesian product
MATCH (a:Person), (b:Product)
WHERE a.name = $name AND b.category = $category
RETURN a, b
-- Returns: |Person| × |Product| rows

-- Good: Connect patterns or use separate queries
MATCH (a:Person {name: $name})-[:PURCHASED]->(b:Product)
WHERE b.category = $category
RETURN a, b
```

### Unbounded Variable-Length Paths

```cypher
-- Bad: Can explode exponentially
MATCH (a)-[*]->(b)
RETURN a, b

-- Good: Bound the path length
MATCH (a)-[*1..5]->(b)
RETURN a, b

-- Better: Use shortestPath for reachability
MATCH path = shortestPath((a)-[*..10]->(b))
RETURN path
```

### COLLECT Then UNWIND

```cypher
-- Bad: Unnecessary aggregation cycle
MATCH (p:Person)-[:KNOWS]->(f:Person)
WITH p, collect(f) AS friends
UNWIND friends AS friend
RETURN p.name, friend.name

-- Good: Just return directly
MATCH (p:Person)-[:KNOWS]->(f:Person)
RETURN p.name, f.name

-- Good: If you need both aggregate and detail
MATCH (p:Person)-[:KNOWS]->(f:Person)
WITH p, collect(f.name) AS friendNames, count(f) AS friendCount
RETURN p.name, friendNames, friendCount
```

### DISTINCT as Band-Aid

```cypher
-- Bad: Using DISTINCT to fix bad pattern
MATCH (a:Person)-[:KNOWS]->(b)-[:KNOWS]->(c)
RETURN DISTINCT c.name
-- DISTINCT hides that you're getting duplicates

-- Good: Fix the underlying pattern
MATCH (a:Person)-[:KNOWS]->(b)
WITH DISTINCT b
MATCH (b)-[:KNOWS]->(c)
RETURN DISTINCT c.name
```

### Multiple Property Access

```cypher
-- Bad: Access node multiple times
MATCH (n:Person)
WHERE n.age > 30
RETURN n.name, n.email, n.age, n.city, n.country

-- Good: Return the node or use map projection
MATCH (n:Person)
WHERE n.age > 30
RETURN n {.name, .email, .age, .city, .country}
```

## Rewrite Patterns

### OR to UNION

```cypher
-- Slow: OR prevents index usage
MATCH (n:Person)
WHERE n.email = $email OR n.phone = $phone
RETURN n

-- Fast: UNION allows index on each
MATCH (n:Person) WHERE n.email = $email RETURN n
UNION
MATCH (n:Person) WHERE n.phone = $phone RETURN n
```

### NOT EXISTS to OPTIONAL MATCH

```cypher
-- Sometimes slow: NOT with exists
MATCH (p:Person)
WHERE NOT exists((p)-[:OWNS]->(:Car))
RETURN p

-- Alternative: OPTIONAL MATCH and filter nulls
MATCH (p:Person)
OPTIONAL MATCH (p)-[:OWNS]->(c:Car)
WITH p, c
WHERE c IS NULL
RETURN p
```

### Aggregation Before Join

```cypher
-- Slow: Join then aggregate
MATCH (p:Person)-[:PURCHASED]->(prod:Product)-[:IN_CATEGORY]->(c:Category)
WHERE c.name = $category
RETURN p.name, count(prod) AS purchaseCount

-- Fast: Aggregate in subquery, then filter
MATCH (prod:Product)-[:IN_CATEGORY]->(c:Category {name: $category})
WITH prod
MATCH (p:Person)-[:PURCHASED]->(prod)
RETURN p.name, count(prod) AS purchaseCount
```

## Memory Management

### Large Result Sets

```cypher
-- Problem: Loading millions of rows
MATCH (n:LogEntry)
RETURN n

-- Solution 1: Pagination
MATCH (n:LogEntry)
RETURN n
ORDER BY n.timestamp
SKIP $offset LIMIT $pageSize

-- Solution 2: Streaming (application-level)
-- Use driver's streaming API instead of loading all at once
```

### Large Aggregations

```cypher
-- Problem: Collecting millions of items
MATCH (p:Person)-[:PURCHASED]->(prod:Product)
RETURN p.name, collect(prod.name) AS products

-- Solution: Limit collection size
MATCH (p:Person)-[:PURCHASED]->(prod:Product)
WITH p, prod
ORDER BY prod.price DESC
WITH p, collect(prod.name)[0..100] AS topProducts
RETURN p.name, topProducts
```

### Batching Writes

```cypher
-- Problem: Updating millions of nodes
MATCH (n:Person)
SET n.processed = true

-- Solution: Batch with LIMIT
CALL apoc.periodic.iterate(
    "MATCH (n:Person) WHERE n.processed IS NULL RETURN n",
    "SET n.processed = true",
    {batchSize: 10000}
)

-- Or manually with LIMIT
MATCH (n:Person)
WHERE n.processed IS NULL
WITH n LIMIT 10000
SET n.processed = true
RETURN count(*)
-- Run repeatedly until count is 0
```

## Query Hints

### Index Hints

```cypher
MATCH (n:Person)
USING INDEX n:Person(email)
WHERE n.email = $email
RETURN n
```

### Scan Hints

```cypher
-- Force label scan when optimizer chooses index incorrectly
MATCH (n:Person)
USING SCAN n:Person
WHERE n.active = true
RETURN n
```

### Join Hints

```cypher
-- Control join order
MATCH (a:Person)-[:KNOWS]->(b:Person)
USING JOIN ON b
WHERE a.name = $name AND b.city = $city
RETURN a, b
```

## Profiling Workflow

1. **Write the query** with correct semantics
2. **EXPLAIN** to see the plan
3. **Look for warning signs** (scans, Cartesian products)
4. **PROFILE** with representative parameters
5. **Compare estimated vs actual rows**
6. **Add indexes** if needed
7. **Rewrite** to eliminate anti-patterns
8. **PROFILE again** to verify improvement
9. **Test with production-like data volume**
