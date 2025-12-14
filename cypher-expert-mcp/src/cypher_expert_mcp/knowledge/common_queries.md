# Common Cypher Query Patterns

50+ annotated Cypher query examples covering common use cases.

## Basic CRUD Operations

### 1. Create a Node

```cypher
CREATE (p:Person {
    id: $id,
    name: $name,
    email: $email,
    createdAt: timestamp()
})
RETURN p
```
**Use case:** Creating new entities with properties.

### 2. Find Node by ID

```cypher
MATCH (n {id: $id})
RETURN n
```
**Use case:** Direct lookup by unique identifier.

### 3. Find Nodes by Label and Property

```cypher
MATCH (p:Person)
WHERE p.email = $email
RETURN p
```
**Use case:** Finding specific entities. Requires index on Person(email) for performance.

### 4. Update Node Properties

```cypher
MATCH (p:Person {id: $id})
SET p.name = $newName,
    p.updatedAt = timestamp()
RETURN p
```
**Use case:** Modifying existing entities.

### 5. Delete Node (with relationships)

```cypher
MATCH (p:Person {id: $id})
DETACH DELETE p
RETURN count(*) AS deleted
```
**Use case:** Removing entities. DETACH removes relationships first.

### 6. Create Relationship

```cypher
MATCH (a:Person {id: $fromId})
MATCH (b:Person {id: $toId})
CREATE (a)-[r:KNOWS {since: $since}]->(b)
RETURN r
```
**Use case:** Connecting entities with relationships.

### 7. Merge (Upsert) Pattern

```cypher
MERGE (p:Person {email: $email})
ON CREATE SET
    p.id = randomUUID(),
    p.name = $name,
    p.createdAt = timestamp()
ON MATCH SET
    p.lastSeen = timestamp()
RETURN p
```
**Use case:** Create if not exists, update if exists.

---

## Traversal Patterns

### 8. Direct Neighbors

```cypher
MATCH (p:Person {id: $id})-[:KNOWS]->(friend:Person)
RETURN friend.name, friend.email
```
**Use case:** Find directly connected nodes.

### 9. Bidirectional Neighbors

```cypher
MATCH (p:Person {id: $id})-[:KNOWS]-(friend:Person)
RETURN DISTINCT friend.name
```
**Use case:** Find connections regardless of relationship direction.

### 10. Friends of Friends

```cypher
MATCH (p:Person {id: $id})-[:KNOWS]->(friend)-[:KNOWS]->(fof:Person)
WHERE p <> fof
  AND NOT (p)-[:KNOWS]->(fof)
RETURN DISTINCT fof.name, count(friend) AS mutualFriends
ORDER BY mutualFriends DESC
LIMIT 10
```
**Use case:** Recommendations based on mutual connections.

### 11. Variable-Length Path

```cypher
MATCH (start:Person {id: $startId})-[:KNOWS*1..3]->(connected:Person)
RETURN DISTINCT connected.id, connected.name
```
**Use case:** Find nodes within N hops.

### 12. Shortest Path

```cypher
MATCH path = shortestPath(
    (a:Person {id: $fromId})-[:KNOWS*..10]-(b:Person {id: $toId})
)
RETURN path,
       [n IN nodes(path) | n.name] AS names,
       length(path) AS hops
```
**Use case:** Find the shortest connection between two nodes.

### 13. All Shortest Paths

```cypher
MATCH paths = allShortestPaths(
    (a:Person {id: $fromId})-[:KNOWS*..10]-(b:Person {id: $toId})
)
RETURN [n IN nodes(paths) | n.name] AS pathNames
```
**Use case:** Find all equally short paths.

### 14. Path with Weighted Edges

```cypher
MATCH path = (a:City {name: $from})-[:ROAD*1..10]->(b:City {name: $to})
WITH path,
     reduce(dist = 0, r IN relationships(path) | dist + r.distance) AS totalDistance
RETURN [n IN nodes(path) | n.name] AS route,
       totalDistance
ORDER BY totalDistance
LIMIT 1
```
**Use case:** Find optimal path by edge weight.

---

## Aggregation Patterns

### 15. Count by Label

```cypher
MATCH (n:Person)
RETURN count(n) AS personCount
```
**Use case:** Get entity counts.

### 16. Count by Property

```cypher
MATCH (p:Person)
RETURN p.city AS city, count(p) AS count
ORDER BY count DESC
```
**Use case:** Group and count by attribute.

### 17. Average, Min, Max

```cypher
MATCH (p:Person)
WHERE p.age IS NOT NULL
RETURN avg(p.age) AS avgAge,
       min(p.age) AS minAge,
       max(p.age) AS maxAge,
       count(p) AS total
```
**Use case:** Statistical aggregations.

### 18. Collect into List

```cypher
MATCH (p:Person)-[:PURCHASED]->(prod:Product)
RETURN p.name,
       collect(prod.name) AS products,
       count(prod) AS productCount
```
**Use case:** Aggregate related items into lists.

### 19. Top N by Count

```cypher
MATCH (prod:Product)<-[:PURCHASED]-(p:Person)
WITH prod, count(p) AS purchaseCount
ORDER BY purchaseCount DESC
LIMIT 10
RETURN prod.name, purchaseCount
```
**Use case:** Find most popular/frequent items.

### 20. Percentile and Distribution

```cypher
MATCH (p:Person)
WHERE p.age IS NOT NULL
WITH p.age AS age
ORDER BY age
WITH collect(age) AS ages
RETURN ages[toInteger(size(ages) * 0.5)] AS median,
       ages[toInteger(size(ages) * 0.9)] AS p90,
       ages[0] AS min,
       ages[size(ages)-1] AS max
```
**Use case:** Distribution analysis.

---

## Filtering Patterns

### 21. Multiple Conditions

```cypher
MATCH (p:Person)
WHERE p.age >= 21
  AND p.age <= 65
  AND p.status = 'active'
  AND p.country IN ['USA', 'Canada', 'UK']
RETURN p
```
**Use case:** Complex filtering.

### 22. Pattern-Based Filter

```cypher
MATCH (p:Person)
WHERE (p)-[:WORKS_AT]->(:Company {name: 'Acme'})
RETURN p.name
```
**Use case:** Filter by existence of relationships.

### 23. Negative Pattern Filter

```cypher
MATCH (p:Person)
WHERE NOT (p)-[:BLOCKED]-()
  AND NOT p.status = 'suspended'
RETURN p
```
**Use case:** Exclude based on patterns.

### 24. String Matching

```cypher
MATCH (p:Person)
WHERE p.name STARTS WITH $prefix
   OR p.name CONTAINS $substring
   OR p.email =~ '.*@company\\.com$'
RETURN p
```
**Use case:** Text search patterns.

### 25. Null Handling

```cypher
MATCH (p:Person)
WHERE p.phone IS NOT NULL
  AND p.verifiedAt IS NOT NULL
RETURN p.name, p.phone
```
**Use case:** Filter by property existence.

---

## Subgraph Extraction

### 26. Node with All Relationships

```cypher
MATCH (p:Person {id: $id})-[r]-(connected)
RETURN p, r, connected
```
**Use case:** Extract a node's immediate neighborhood.

### 27. Ego Network (N-hop subgraph)

```cypher
MATCH path = (center:Person {id: $id})-[*1..2]-(neighbor)
WITH collect(DISTINCT nodes(path)) AS nodeLists
UNWIND nodeLists AS nodeList
UNWIND nodeList AS node
WITH collect(DISTINCT node) AS subgraphNodes
MATCH (a)-[r]-(b)
WHERE a IN subgraphNodes AND b IN subgraphNodes
RETURN DISTINCT a, r, b
```
**Use case:** Extract subgraph around a central node.

### 28. Community Subgraph

```cypher
MATCH (p:Person)-[:MEMBER_OF]->(g:Group {id: $groupId})
WITH collect(p) AS members
MATCH (a:Person)-[r:KNOWS]-(b:Person)
WHERE a IN members AND b IN members
RETURN a, r, b
```
**Use case:** Extract connections within a community.

---

## Graph Analytics Patterns

### 29. Degree Centrality

```cypher
MATCH (p:Person)
OPTIONAL MATCH (p)-[r]-()
RETURN p.name,
       count(r) AS degree
ORDER BY degree DESC
LIMIT 20
```
**Use case:** Find most connected nodes.

### 30. In-Degree vs Out-Degree

```cypher
MATCH (p:Person)
OPTIONAL MATCH (p)-[out]->()
OPTIONAL MATCH (p)<-[in]-()
RETURN p.name,
       count(DISTINCT out) AS outDegree,
       count(DISTINCT in) AS inDegree
ORDER BY inDegree DESC
```
**Use case:** Analyze directional connectivity.

### 31. Triangle Count

```cypher
MATCH (a:Person)-[:KNOWS]-(b:Person)-[:KNOWS]-(c:Person)-[:KNOWS]-(a)
WHERE id(a) < id(b) AND id(b) < id(c)
RETURN count(*) AS triangles
```
**Use case:** Measure graph clustering.

### 32. Local Clustering Coefficient

```cypher
MATCH (p:Person {id: $id})-[:KNOWS]-(neighbor)
WITH p, collect(neighbor) AS neighbors, count(neighbor) AS k
WHERE k > 1
MATCH (a)-[:KNOWS]-(b)
WHERE a IN neighbors AND b IN neighbors AND id(a) < id(b)
WITH p, k, count(*) AS triangles
RETURN p.name,
       2.0 * triangles / (k * (k - 1)) AS clusteringCoeff
```
**Use case:** Measure how connected a node's neighbors are.

### 33. Weakly Connected Components (simple)

```cypher
MATCH (start:Person)
WHERE NOT (:Person)-[:KNOWS]->(start)
MATCH path = (start)-[:KNOWS*0..100]->(member:Person)
RETURN start.id AS componentRoot,
       collect(DISTINCT member.id) AS members
```
**Use case:** Find disconnected components (simplified).

---

## Time-Based Patterns

### 34. Recent Activity

```cypher
MATCH (p:Person)-[r:PURCHASED]->(prod:Product)
WHERE r.timestamp > timestamp() - (24 * 60 * 60 * 1000)  // Last 24 hours
RETURN p.name, prod.name, r.timestamp
ORDER BY r.timestamp DESC
```
**Use case:** Find recent events.

### 35. Activity Over Time

```cypher
MATCH (p:Person)-[r:PURCHASED]->(:Product)
WITH p,
     (r.timestamp / (24 * 60 * 60 * 1000)) AS dayNumber
RETURN dayNumber,
       count(DISTINCT p) AS activeUsers,
       count(r) AS purchases
ORDER BY dayNumber
```
**Use case:** Time series aggregation.

### 36. Retention Analysis

```cypher
// Users who purchased in week 1 and returned in week 2
MATCH (p:Person)-[r1:PURCHASED]->(:Product)
WHERE r1.timestamp >= $week1Start AND r1.timestamp < $week1End
WITH DISTINCT p
MATCH (p)-[r2:PURCHASED]->(:Product)
WHERE r2.timestamp >= $week2Start AND r2.timestamp < $week2End
RETURN count(DISTINCT p) AS returnedUsers
```
**Use case:** User retention metrics.

---

## Hierarchical Data

### 37. Tree Traversal (Parent to Children)

```cypher
MATCH (parent:Category {id: $parentId})-[:HAS_CHILD*1..5]->(descendant:Category)
RETURN descendant.id, descendant.name
```
**Use case:** Navigate tree structures.

### 38. Find Ancestors

```cypher
MATCH (child:Category {id: $childId})<-[:HAS_CHILD*1..10]-(ancestor:Category)
RETURN ancestor.id, ancestor.name
```
**Use case:** Find all ancestors in hierarchy.

### 39. Tree Depth

```cypher
MATCH path = (root:Category)-[:HAS_CHILD*]->(leaf:Category)
WHERE NOT (root)<-[:HAS_CHILD]-()
  AND NOT (leaf)-[:HAS_CHILD]->()
RETURN root.name AS root,
       leaf.name AS leaf,
       length(path) AS depth
ORDER BY depth DESC
```
**Use case:** Analyze tree structure depth.

### 40. Siblings

```cypher
MATCH (node:Category {id: $id})<-[:HAS_CHILD]-(parent)-[:HAS_CHILD]->(sibling)
WHERE sibling <> node
RETURN sibling.id, sibling.name
```
**Use case:** Find nodes at same level.

---

## Recommendation Patterns

### 41. Collaborative Filtering

```cypher
// Users who bought X also bought Y
MATCH (p:Person)-[:PURCHASED]->(target:Product {id: $productId})
MATCH (p)-[:PURCHASED]->(other:Product)
WHERE other <> target
RETURN other.name,
       count(p) AS coOccurrence
ORDER BY coOccurrence DESC
LIMIT 10
```
**Use case:** "Customers also bought" recommendations.

### 42. Content-Based Similarity

```cypher
MATCH (target:Product {id: $productId})-[:IN_CATEGORY]->(cat:Category)
MATCH (similar:Product)-[:IN_CATEGORY]->(cat)
WHERE similar <> target
WITH similar, count(cat) AS sharedCategories
ORDER BY sharedCategories DESC
LIMIT 10
RETURN similar.name, sharedCategories
```
**Use case:** Find similar items by attributes.

### 43. Personalized Recommendations

```cypher
MATCH (user:Person {id: $userId})-[:PURCHASED]->(bought:Product)
MATCH (bought)-[:IN_CATEGORY]->(cat:Category)<-[:IN_CATEGORY]-(rec:Product)
WHERE NOT (user)-[:PURCHASED]->(rec)
WITH rec, count(DISTINCT cat) AS relevance, collect(DISTINCT cat.name) AS categories
ORDER BY relevance DESC
LIMIT 20
RETURN rec.name, relevance, categories
```
**Use case:** Personalized product recommendations.

---

## Access Control Patterns

### 44. Check Permission

```cypher
MATCH (user:User {id: $userId})-[:HAS_ROLE]->(role:Role)-[:HAS_PERMISSION]->(perm:Permission)
WHERE perm.name = $permissionName
RETURN count(perm) > 0 AS hasPermission
```
**Use case:** Authorization check.

### 45. Inherited Permissions

```cypher
MATCH (user:User {id: $userId})-[:HAS_ROLE]->(role:Role)
MATCH (role)-[:INHERITS*0..5]->(parentRole:Role)-[:HAS_PERMISSION]->(perm:Permission)
RETURN DISTINCT perm.name AS permission
```
**Use case:** Role hierarchy with inherited permissions.

### 46. Access Path

```cypher
MATCH (user:User {id: $userId})-[:MEMBER_OF*1..3]->(group:Group)-[:HAS_ACCESS]->(resource:Resource {id: $resourceId})
RETURN count(*) > 0 AS hasAccess,
       [n IN nodes(path) | labels(n)[0] + ': ' + n.name] AS accessPath
```
**Use case:** Determine access through group membership.

---

## Data Quality Patterns

### 47. Find Orphan Nodes

```cypher
MATCH (n)
WHERE NOT (n)-[]-()
RETURN labels(n) AS type, count(n) AS orphanCount
```
**Use case:** Find disconnected nodes.

### 48. Find Duplicate Nodes

```cypher
MATCH (p:Person)
WITH p.email AS email, collect(p) AS nodes, count(p) AS count
WHERE count > 1
RETURN email, count, [n IN nodes | n.id] AS duplicateIds
```
**Use case:** Identify duplicate entities.

### 49. Missing Required Relationships

```cypher
MATCH (p:Person)
WHERE NOT (p)-[:WORKS_AT]->(:Company)
RETURN p.id, p.name
LIMIT 100
```
**Use case:** Find incomplete data.

### 50. Schema Validation

```cypher
MATCH (p:Person)
WHERE p.email IS NULL
   OR NOT p.email =~ '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'
RETURN p.id, p.email AS invalidEmail
```
**Use case:** Validate data format.

---

## Bulk Operations

### 51. Batch Update

```cypher
MATCH (p:Person)
WHERE p.status = 'pending' AND p.createdAt < $cutoffTime
WITH p LIMIT 1000
SET p.status = 'expired'
RETURN count(p) AS updated
```
**Use case:** Update many nodes in batches.

### 52. Batch Delete

```cypher
MATCH (n:TempNode)
WHERE n.expiresAt < timestamp()
WITH n LIMIT 1000
DETACH DELETE n
RETURN count(*) AS deleted
```
**Use case:** Clean up expired data.

### 53. Copy Subgraph

```cypher
MATCH (original:Template {id: $templateId})-[r*1..3]->(connected)
WITH original, collect(DISTINCT connected) + [original] AS nodesToCopy
UNWIND nodesToCopy AS node
CREATE (copy:Copy)
SET copy = properties(node), copy.originalId = node.id
RETURN count(copy) AS copiedNodes
```
**Use case:** Clone a portion of the graph.

---

## Virtue Basin Specific Patterns

### 54. Activation Spread

```cypher
MATCH (source {id: $sourceId})-[r]-(neighbor)
WHERE r.weight > $threshold
WITH neighbor, r.weight AS weight
ORDER BY weight DESC
LIMIT $maxNeighbors
SET neighbor.activation = neighbor.activation + ($sourceActivation * weight * $spreadRate)
RETURN neighbor.id, neighbor.activation
```
**Use case:** Spread activation through weighted edges.

### 55. Virtue Capture Detection

```cypher
MATCH (concept:Concept {id: $conceptId})-[r:CONNECTS*1..3]-(v:VirtueAnchor)
WITH v, min(length(r)) AS distance,
     sum([rel IN r | rel.weight]) AS pathStrength
WHERE pathStrength > $captureThreshold
RETURN v.id AS capturedVirtue,
       distance,
       pathStrength
ORDER BY pathStrength DESC
```
**Use case:** Detect which virtue basins capture a concept.

### 56. Coherence Testing

```cypher
MATCH (v:VirtueAnchor)
OPTIONAL MATCH (v)<-[r:CONNECTS*1..3]-(concept:Concept)
WHERE concept.activated = true
WITH v,
     count(DISTINCT concept) AS activatedConcepts,
     sum([rel IN r | rel.weight]) AS totalWeight
RETURN v.id AS virtue,
       activatedConcepts,
       totalWeight,
       CASE WHEN activatedConcepts > 0
            THEN totalWeight / activatedConcepts
            ELSE 0 END AS avgStrength
ORDER BY avgStrength DESC
```
**Use case:** Measure virtue basin activation coherence.
