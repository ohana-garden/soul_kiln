# Cypher Query Language Reference

A comprehensive reference for Cypher, the graph query language used by Neo4j and FalkorDB.

## Clauses

### Reading Clauses

#### MATCH
Pattern matching against the graph.

```cypher
-- Basic node match
MATCH (n:Person)
RETURN n

-- Match with relationship
MATCH (a:Person)-[:KNOWS]->(b:Person)
RETURN a, b

-- Variable-length paths
MATCH (a)-[*1..3]->(b)
RETURN a, b

-- Named path
MATCH path = (a)-[:KNOWS*]->(b)
RETURN path
```

#### OPTIONAL MATCH
Like MATCH, but returns null for missing patterns instead of filtering out.

```cypher
MATCH (p:Person)
OPTIONAL MATCH (p)-[:OWNS]->(c:Car)
RETURN p.name, c.model
-- Returns person even if they don't own a car (c.model = null)
```

#### WHERE
Filter results from MATCH.

```cypher
MATCH (n:Person)
WHERE n.age > 30 AND n.name STARTS WITH 'A'
RETURN n

-- Pattern predicates in WHERE
MATCH (n:Person)
WHERE (n)-[:KNOWS]->(:Developer)
RETURN n

-- NOT patterns
MATCH (n:Person)
WHERE NOT (n)-[:BLOCKED]-()
RETURN n
```

### Writing Clauses

#### CREATE
Create nodes and relationships.

```cypher
-- Create node
CREATE (n:Person {name: 'Alice', age: 30})

-- Create relationship
MATCH (a:Person {name: 'Alice'}), (b:Person {name: 'Bob'})
CREATE (a)-[:KNOWS {since: 2020}]->(b)

-- Create with RETURN
CREATE (n:Person {name: 'Charlie'})
RETURN n
```

#### MERGE
Create if not exists, match if exists.

```cypher
-- Merge node
MERGE (n:Person {email: 'alice@example.com'})
ON CREATE SET n.created = timestamp()
ON MATCH SET n.lastSeen = timestamp()
RETURN n

-- Merge relationship
MATCH (a:Person {name: 'Alice'}), (b:Person {name: 'Bob'})
MERGE (a)-[r:KNOWS]->(b)
ON CREATE SET r.since = date()
RETURN r
```

#### SET
Set properties on nodes or relationships.

```cypher
MATCH (n:Person {name: 'Alice'})
SET n.age = 31, n.updated = timestamp()
RETURN n

-- Set multiple properties from map
MATCH (n:Person {name: 'Alice'})
SET n += {city: 'NYC', country: 'USA'}
RETURN n

-- Add label
MATCH (n:Person {name: 'Alice'})
SET n:Employee
RETURN n
```

#### DELETE / DETACH DELETE
Remove nodes and relationships.

```cypher
-- Delete node (must have no relationships)
MATCH (n:TempNode)
DELETE n

-- Delete node and all relationships
MATCH (n:Person {name: 'Alice'})
DETACH DELETE n

-- Delete relationship only
MATCH (a:Person)-[r:KNOWS]->(b:Person)
WHERE a.name = 'Alice' AND b.name = 'Bob'
DELETE r
```

#### REMOVE
Remove properties or labels.

```cypher
-- Remove property
MATCH (n:Person {name: 'Alice'})
REMOVE n.age
RETURN n

-- Remove label
MATCH (n:Person:Employee {name: 'Alice'})
REMOVE n:Employee
RETURN n
```

### Projection Clauses

#### RETURN
Specify what to return.

```cypher
MATCH (n:Person)
RETURN n.name, n.age

-- Aliasing
RETURN n.name AS personName

-- Distinct results
RETURN DISTINCT n.city

-- Return everything
RETURN *

-- Aggregation in return
RETURN n.city, count(*) AS population
```

#### WITH
Chain query parts, create intermediate results.

```cypher
MATCH (p:Person)
WITH p, size((p)-[:KNOWS]->()) AS friendCount
WHERE friendCount > 5
RETURN p.name, friendCount

-- Aggregate then filter
MATCH (p:Person)-[:PURCHASED]->(prod:Product)
WITH p, count(prod) AS purchaseCount
WHERE purchaseCount > 10
RETURN p.name, purchaseCount
ORDER BY purchaseCount DESC
```

#### UNWIND
Expand a list into rows.

```cypher
UNWIND [1, 2, 3] AS x
RETURN x

-- Create nodes from list
UNWIND $names AS name
CREATE (n:Person {name: name})

-- Flatten nested lists
MATCH (p:Person)
UNWIND p.hobbies AS hobby
RETURN DISTINCT hobby
```

### Result Modifiers

#### ORDER BY
Sort results.

```cypher
MATCH (n:Person)
RETURN n.name, n.age
ORDER BY n.age DESC, n.name ASC
```

#### SKIP / LIMIT
Pagination.

```cypher
MATCH (n:Person)
RETURN n.name
ORDER BY n.name
SKIP 10
LIMIT 10
```

#### UNION / UNION ALL
Combine query results.

```cypher
MATCH (a:Person) RETURN a.name AS name
UNION
MATCH (b:Company) RETURN b.name AS name

-- Keep duplicates
MATCH (a:Person) RETURN a.name
UNION ALL
MATCH (b:Person) RETURN b.name
```

## Functions

### Aggregation Functions

```cypher
count(*)           -- Count rows
count(n)           -- Count non-null values
count(DISTINCT n)  -- Count unique values
sum(n.value)       -- Sum numeric values
avg(n.value)       -- Average
min(n.value)       -- Minimum
max(n.value)       -- Maximum
collect(n)         -- Collect into list
collect(DISTINCT n) -- Collect unique values
```

### String Functions

```cypher
toString(value)         -- Convert to string
toUpper(s)              -- Uppercase
toLower(s)              -- Lowercase
trim(s)                 -- Trim whitespace
ltrim(s), rtrim(s)      -- Left/right trim
replace(s, from, to)    -- Replace substring
substring(s, start, len) -- Extract substring
split(s, delimiter)     -- Split into list
size(s)                 -- String length
left(s, n), right(s, n) -- First/last n characters
```

### List Functions

```cypher
size(list)              -- List length
head(list)              -- First element
tail(list)              -- All but first
last(list)              -- Last element
range(start, end)       -- Generate range [start, end]
range(start, end, step) -- With step
reverse(list)           -- Reverse list
[x IN list WHERE pred]  -- List comprehension
[x IN list | expr]      -- Map over list
```

### Mathematical Functions

```cypher
abs(n)                  -- Absolute value
ceil(n), floor(n)       -- Round up/down
round(n)                -- Round to nearest
round(n, precision)     -- Round to precision
sqrt(n)                 -- Square root
sign(n)                 -- Sign (-1, 0, 1)
rand()                  -- Random [0, 1)
```

### Path Functions

```cypher
length(path)            -- Number of relationships
nodes(path)             -- List of nodes
relationships(path)     -- List of relationships
```

### Node/Relationship Functions

```cypher
id(node)                -- Internal ID
labels(node)            -- List of labels
type(relationship)      -- Relationship type
properties(n)           -- Map of properties
keys(n)                 -- List of property keys
```

### Predicate Functions

```cypher
exists(n.prop)          -- Property exists
all(x IN list WHERE pred)  -- All satisfy predicate
any(x IN list WHERE pred)  -- Any satisfies predicate
none(x IN list WHERE pred) -- None satisfy predicate
single(x IN list WHERE pred) -- Exactly one satisfies
```

### Date/Time Functions

```cypher
date()                  -- Current date
datetime()              -- Current datetime
timestamp()             -- Milliseconds since epoch
duration('P1D')         -- Duration of 1 day
date() - duration('P30D') -- 30 days ago
```

## Operators

### Comparison
```cypher
=, <>, <, >, <=, >=
IS NULL, IS NOT NULL
```

### Boolean
```cypher
AND, OR, NOT, XOR
```

### String
```cypher
STARTS WITH, ENDS WITH, CONTAINS
=~ 'regex'  -- Regular expression match
```

### List
```cypher
IN           -- Element in list
+            -- Concatenate lists
list[0]      -- Index access
list[1..3]   -- Slice
```

### Mathematical
```cypher
+, -, *, /, %, ^
```

## Pattern Syntax

### Node Patterns
```cypher
(n)                    -- Any node
(n:Label)              -- Node with label
(n:Label1:Label2)      -- Multiple labels
(n {prop: value})      -- With properties
(n:Label {prop: $param}) -- Label and properties
```

### Relationship Patterns
```cypher
-[r]->                 -- Outgoing
<-[r]-                 -- Incoming
-[r]-                  -- Either direction
-[r:TYPE]->            -- With type
-[r:TYPE1|TYPE2]->     -- Multiple types
-[r {prop: value}]->   -- With properties
-[r*]->                -- Variable length (avoid!)
-[r*1..5]->            -- Bounded variable length
-[r*..5]->             -- Up to 5
-[r*3..]->             -- At least 3
```

### Path Patterns
```cypher
(a)-[*]->(b)           -- Any path (dangerous)
(a)-[*1..10]->(b)      -- Bounded path
shortestPath((a)-[*]->(b))  -- Shortest path
allShortestPaths((a)-[*]->(b))  -- All shortest
```

## Parameters

Always use parameters for user input:

```cypher
-- Good: parameterized
MATCH (n:Person) WHERE n.email = $email RETURN n

-- Bad: string interpolation (injection risk!)
MATCH (n:Person) WHERE n.email = 'user@example.com' RETURN n
```

Parameter syntax:
- `$paramName` - Named parameter
- `$0`, `$1` - Positional parameters (some drivers)

## Query Plan Operators

When using EXPLAIN or PROFILE:

| Operator | Description | Performance Note |
|----------|-------------|------------------|
| AllNodesScan | Scan all nodes | Very slow for large graphs |
| NodeByLabelScan | Scan all nodes with label | Slow without index |
| NodeIndexSeek | Use index to find nodes | Fast |
| NodeUniqueIndexSeek | Use unique index | Very fast |
| Expand | Traverse relationships | Depends on cardinality |
| Filter | Apply WHERE conditions | After data fetch |
| Projection | Select properties | Usually cheap |
| Sort | ORDER BY | Can be expensive |
| EagerAggregation | Aggregation functions | Memory intensive |

## Best Practices

1. **Always use parameters** for user input
2. **Add indexes** for frequently queried properties
3. **Bound variable-length paths** to prevent runaway queries
4. **Use LIMIT** when you don't need all results
5. **Filter early** with WHERE close to MATCH
6. **Use WITH** to checkpoint and reduce intermediate results
7. **Avoid Cartesian products** - ensure MATCH patterns connect
8. **Profile queries** before production use
