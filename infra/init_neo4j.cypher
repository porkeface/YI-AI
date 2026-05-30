// Neo4j Schema Initialization for YI-AI Knowledge Graph
// Creates indexes and constraints for the Yi-Jing knowledge graph

// Unique constraints on node IDs
CREATE CONSTRAINT hexagram_id IF NOT EXISTS FOR (n:hexagram) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT line_id IF NOT EXISTS FOR (n:line) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT trigram_id IF NOT EXISTS FOR (n:trigram) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT element_id IF NOT EXISTS FOR (n:element) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT palace_id IF NOT EXISTS FOR (n:palace) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT concept_id IF NOT EXISTS FOR (n:concept) REQUIRE n.id IS UNIQUE;

// Indexes for common lookups
CREATE INDEX hexagram_name IF NOT EXISTS FOR (n:hexagram) ON (n.name);
CREATE INDEX line_position IF NOT EXISTS FOR (n:line) ON (n.position);
CREATE INDEX trigram_name IF NOT EXISTS FOR (n:trigram) ON (n.name);
CREATE INDEX element_name IF NOT EXISTS FOR (n:element) ON (n.name);
