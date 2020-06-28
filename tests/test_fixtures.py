import uuid

import models


def test_initialization(driver_a):
    """ Tests fixture gets initialized correctly

    Args:
        driver_a (psqlgraph.PsqlGraphDriver): pg driver

    """
    with driver_a.session_scope() as s:
        x = driver_a.nodes(models.Mother).count()
        assert 0 == x

        # create mother entry
        mother = models.Mother(
            node_id=str(uuid.uuid4()),
            name="Isioma M. E."
        )
        s.add(mother)

    with driver_a.session_scope() as s:
        x = driver_a.nodes(models.Mother).all()
        assert 1 == len(x)
        mom = x[0]
        assert mom.node_id == mother.node_id
        assert mom.name == mother.name


def test_again(driver_fixture):
    print(driver_fixture)
