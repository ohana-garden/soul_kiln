"""Tests for Hawaiian garden plant agents."""

import pytest

from src.agents.plants import (
    PlantAgent,
    PlantGarden,
    PlantDefinition,
    PlantPersonality,
    PlantArchetype,
    TARO,
    TI,
    PLUMERIA,
    HIBISCUS,
    COCONUT,
    BANANA,
    MONSTERA,
    BREADFRUIT,
    RED_GINGER,
    BIRD_OF_PARADISE,
    PIKAKE,
    ALL_PLANTS,
    PLANT_REGISTRY,
    VIRTUE_MAP,
    create_plant_agent,
    create_all_plant_agents,
    create_full_garden,
)


class TestPlantDefinitions:
    """Tests for plant definitions."""

    def test_all_plants_defined(self):
        """Test all 11 plants are defined."""
        assert len(ALL_PLANTS) == 11

    def test_plant_registry_has_aliases(self):
        """Test plant registry includes Hawaiian and English names."""
        # Hawaiian names
        assert "kalo" in PLANT_REGISTRY
        assert "ki" in PLANT_REGISTRY
        assert "niu" in PLANT_REGISTRY
        assert "maia" in PLANT_REGISTRY
        assert "ulu" in PLANT_REGISTRY

        # English names
        assert "taro" in PLANT_REGISTRY
        assert "ti" in PLANT_REGISTRY
        assert "coconut" in PLANT_REGISTRY
        assert "banana" in PLANT_REGISTRY
        assert "breadfruit" in PLANT_REGISTRY

    def test_taro_definition(self):
        """Test Taro (Kalo) definition."""
        assert TARO.id == "plant_taro"
        assert TARO.hawaiian_name == "Kalo"
        assert TARO.english_name == "Taro"
        assert TARO.personality.archetype == PlantArchetype.ELDER
        assert "nurturing" in TARO.personality.traits
        assert "V18" in TARO.personality.primary_virtues  # Unity

    def test_ti_definition(self):
        """Test Ti (Ki) definition."""
        assert TI.id == "plant_ti"
        assert TI.hawaiian_name == "Kī"
        assert TI.personality.archetype == PlantArchetype.GUARDIAN
        assert "protective" in TI.personality.traits
        assert "V08" in TI.personality.primary_virtues  # Fidelity

    def test_plumeria_definition(self):
        """Test Plumeria (Melia) definition."""
        assert PLUMERIA.hawaiian_name == "Melia"
        assert PLUMERIA.personality.archetype == PlantArchetype.WELCOMER
        assert "welcoming" in PLUMERIA.personality.traits
        assert "V09" in PLUMERIA.personality.primary_virtues  # Hospitality

    def test_hibiscus_definition(self):
        """Test Hibiscus (Aloalo) definition."""
        assert HIBISCUS.hawaiian_name == "Aloalo"
        assert HIBISCUS.personality.archetype == PlantArchetype.RADIANT
        assert "radiant" in HIBISCUS.personality.traits
        assert "V13" in HIBISCUS.personality.primary_virtues  # Goodwill

    def test_each_plant_has_virtues(self):
        """Test each plant has primary, secondary, and tertiary virtues."""
        for plant in ALL_PLANTS:
            assert len(plant.personality.primary_virtues) >= 3
            assert len(plant.personality.secondary_virtues) >= 3
            assert len(plant.personality.tertiary_virtues) >= 3

    def test_virtue_ids_valid(self):
        """Test all virtue IDs are valid (V01-V19)."""
        valid_virtues = {f"V{i:02d}" for i in range(1, 20)}
        for plant in ALL_PLANTS:
            all_virtues = (
                plant.personality.primary_virtues +
                plant.personality.secondary_virtues +
                plant.personality.tertiary_virtues
            )
            for virtue_id in all_virtues:
                assert virtue_id in valid_virtues, f"Invalid virtue {virtue_id} in {plant.english_name}"


class TestPlantAgent:
    """Tests for PlantAgent class."""

    def test_create_agent(self):
        """Test creating a plant agent."""
        agent = PlantAgent(TARO)
        assert agent.id == "plant_taro"
        assert agent.hawaiian_name == "Kalo"
        assert agent.english_name == "Taro"
        assert agent.archetype == PlantArchetype.ELDER

    def test_agent_topology_created(self):
        """Test agent topology is automatically created."""
        agent = PlantAgent(TARO)
        assert len(agent.topology.edges) > 0

    def test_agent_custom_id(self):
        """Test creating agent with custom ID."""
        agent = PlantAgent(TARO, agent_id="custom_taro_001")
        assert agent.id == "custom_taro_001"

    def test_agent_traits(self):
        """Test agent traits are accessible."""
        agent = PlantAgent(TARO)
        assert "nurturing" in agent.traits
        assert "resilient" in agent.traits

    def test_agent_description(self):
        """Test agent description is accessible."""
        agent = PlantAgent(PLUMERIA)
        assert "welcoming" in agent.description.lower()
        assert "aloha" in agent.description.lower()

    def test_agent_virtue_affinities(self):
        """Test virtue affinities are calculated correctly."""
        agent = PlantAgent(TARO)
        affinities = agent.get_virtue_affinities()

        # Primary virtues should have highest affinity
        assert affinities["V18"] == 0.9  # Unity
        assert affinities["V01"] == 0.9  # Trustworthiness

        # Secondary virtues should have medium affinity
        assert affinities["V16"] == 0.65  # Wisdom

        # Tertiary should have lower
        assert affinities["V13"] == 0.4  # Goodwill

    def test_agent_dominant_virtues(self):
        """Test getting dominant virtues."""
        agent = PlantAgent(HIBISCUS)
        dominant = agent.get_dominant_virtues()
        assert "V13" in dominant  # Goodwill
        assert "V18" in dominant  # Unity

    def test_agent_edge_access(self):
        """Test edge access in agent topology."""
        agent = PlantAgent(COCONUT)
        # Primary virtues should be connected
        edge = agent.get_edge("V19", "V09")  # Service -> Hospitality
        assert edge is not None
        assert edge.weight > 0.7

    def test_agent_set_fitness(self):
        """Test setting fitness score."""
        agent = PlantAgent(TARO)
        agent.set_fitness(0.95, {"character_signature": {"V18": 0.9}})
        assert agent.fitness == 0.95
        assert agent.get_character_signature()["V18"] == 0.9

    def test_agent_export(self):
        """Test exporting agent state."""
        agent = PlantAgent(PIKAKE)
        agent.set_fitness(0.88)
        export = agent.export()

        assert export["id"] == "plant_pikake"
        assert export["hawaiian_name"] == "Pīkake"
        assert export["archetype"] == "romantic"
        assert export["fitness"] == 0.88
        assert len(export["edges"]) > 0
        assert len(export["virtue_affinities"]) > 0

    def test_agent_repr(self):
        """Test string representation."""
        agent = PlantAgent(MONSTERA)
        repr_str = repr(agent)
        assert "Monstera" in repr_str
        assert "explorer" in repr_str


class TestPlantTopology:
    """Tests for plant topology generation."""

    def test_primary_virtue_connections(self):
        """Test primary virtues are strongly connected."""
        agent = PlantAgent(BREADFRUIT)
        # Primary: V19, V13, V15 - Service, Goodwill, Righteousness
        edge = agent.get_edge("V19", "V13")
        assert edge is not None
        assert edge.weight >= 0.8

    def test_secondary_to_primary_connections(self):
        """Test secondary virtues connect to primary."""
        agent = PlantAgent(RED_GINGER)
        # Primary: V09 (Hospitality), Secondary: V13 (Goodwill)
        edge = agent.get_edge("V09", "V13")
        assert edge is not None
        assert 0.5 <= edge.weight <= 0.8

    def test_all_agents_have_edges(self):
        """Test all agents have meaningful edge counts."""
        for plant_def in ALL_PLANTS:
            agent = PlantAgent(plant_def)
            # Should have a reasonable number of edges
            assert len(agent.topology.edges) >= 20, f"{plant_def.english_name} has too few edges"


class TestPlantGarden:
    """Tests for PlantGarden class."""

    def test_create_garden(self):
        """Test creating a garden."""
        garden = PlantGarden("Test Garden")
        assert garden.name == "Test Garden"
        assert garden.size == 0

    def test_add_plant(self):
        """Test adding plants to garden."""
        garden = PlantGarden()
        agent = PlantAgent(TARO)
        garden.add_plant(agent)
        assert garden.size == 1
        assert garden.get_plant("plant_taro") is not None

    def test_remove_plant(self):
        """Test removing plant from garden."""
        garden = PlantGarden()
        garden.add_plant(PlantAgent(TARO))
        assert garden.remove_plant("plant_taro") is True
        assert garden.size == 0
        assert garden.remove_plant("nonexistent") is False

    def test_get_plant_by_name(self):
        """Test finding plant by name."""
        garden = PlantGarden()
        garden.add_plant(PlantAgent(PLUMERIA))
        garden.add_plant(PlantAgent(HIBISCUS))

        # By Hawaiian name
        plant = garden.get_plant_by_name("Melia")
        assert plant is not None
        assert plant.english_name == "Plumeria"

        # By English name
        plant = garden.get_plant_by_name("hibiscus")
        assert plant is not None
        assert plant.hawaiian_name == "Aloalo"

    def test_get_plants_by_archetype(self):
        """Test filtering by archetype."""
        garden = PlantGarden()
        garden.add_plant(PlantAgent(TARO))  # ELDER
        garden.add_plant(PlantAgent(TI))  # GUARDIAN
        garden.add_plant(PlantAgent(COCONUT))  # PROVIDER

        elders = garden.get_plants_by_archetype(PlantArchetype.ELDER)
        assert len(elders) == 1
        assert elders[0].english_name == "Taro"

    def test_collective_virtue_profile(self):
        """Test computing collective virtue profile."""
        garden = PlantGarden()
        garden.add_plant(PlantAgent(TARO))
        garden.add_plant(PlantAgent(BANANA))

        profile = garden.get_collective_virtue_profile()
        # Both have Unity (V18) as primary, so it should be high
        assert profile["V18"] > 0.5

    def test_plants_strong_in_virtue(self):
        """Test finding plants strong in a virtue."""
        garden = PlantGarden()
        garden.add_plant(PlantAgent(PLUMERIA))  # Hospitality primary
        garden.add_plant(PlantAgent(RED_GINGER))  # Hospitality primary
        garden.add_plant(PlantAgent(TARO))  # Unity primary

        hospitable = garden.get_plants_strong_in_virtue("V09", threshold=0.8)
        assert len(hospitable) == 2

    def test_garden_export(self):
        """Test exporting garden state."""
        garden = PlantGarden("Aloha Garden")
        garden.add_plant(PlantAgent(TARO))
        garden.add_plant(PlantAgent(TI))

        export = garden.export()
        assert export["name"] == "Aloha Garden"
        assert export["plant_count"] == 2
        assert len(export["plants"]) == 2
        assert "collective_virtue_profile" in export


class TestPlantFactory:
    """Tests for plant factory functions."""

    def test_create_plant_by_english_name(self):
        """Test creating plant by English name."""
        agent = create_plant_agent("Taro")
        assert agent.hawaiian_name == "Kalo"

    def test_create_plant_by_hawaiian_name(self):
        """Test creating plant by Hawaiian name."""
        agent = create_plant_agent("kalo")
        assert agent.english_name == "Taro"

    def test_create_plant_case_insensitive(self):
        """Test case insensitivity."""
        agent1 = create_plant_agent("HIBISCUS")
        agent2 = create_plant_agent("hibiscus")
        assert agent1.hawaiian_name == agent2.hawaiian_name

    def test_create_unknown_plant_raises(self):
        """Test creating unknown plant raises error."""
        with pytest.raises(ValueError) as exc_info:
            create_plant_agent("Unknown Plant")
        assert "Unknown plant" in str(exc_info.value)

    def test_create_all_plant_agents(self):
        """Test creating all plant agents."""
        agents = create_all_plant_agents()
        assert len(agents) == 11
        names = {a.english_name for a in agents}
        assert "Taro" in names
        assert "Plumeria" in names
        assert "Hawaiian Jasmine" in names  # Pikake

    def test_create_full_garden(self):
        """Test creating full garden."""
        garden = create_full_garden()
        assert garden.size == 11
        assert garden.name == "Complete Hawaiian Garden"


class TestPlantArchetypes:
    """Tests for plant archetype coverage."""

    def test_all_archetypes_represented(self):
        """Test each archetype has at least one plant."""
        archetypes_found = {plant.personality.archetype for plant in ALL_PLANTS}
        for archetype in PlantArchetype:
            assert archetype in archetypes_found, f"Archetype {archetype} not represented"

    def test_archetype_distribution(self):
        """Test archetype distribution across plants."""
        archetype_counts = {}
        for plant in ALL_PLANTS:
            arch = plant.personality.archetype
            archetype_counts[arch] = archetype_counts.get(arch, 0) + 1

        # Each archetype should appear once (11 plants, 11 archetypes)
        assert len(archetype_counts) == 11


class TestVirtueMapping:
    """Tests for virtue mapping constants."""

    def test_virtue_map_complete(self):
        """Test virtue map has all 19 virtues."""
        assert len(VIRTUE_MAP) == 19

    def test_virtue_map_ids_valid(self):
        """Test virtue map IDs are valid."""
        for name, vid in VIRTUE_MAP.items():
            assert vid.startswith("V")
            num = int(vid[1:])
            assert 1 <= num <= 19
