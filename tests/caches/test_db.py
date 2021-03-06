import pytest
from aiohttp.test_utils import make_mocked_coro

import virtool.caches.db
import virtool.utils


@pytest.fixture
def create_result(static_time, trim_parameters):
    return {
        "created_at": static_time.datetime,
        "files": [],
        "hash": "68b60be51a667882d3aaa02a93259dd526e9c990",
        "legacy": False,
        "paired": False,
        "parameters": trim_parameters,
        "program": "skewer-0.2.2",
        "ready": False,
        "sample": {
            "id": "foo"
        }
    }


@pytest.fixture
def trim_parameters():
    return {
        "end_quality": "20",
        "mode": "pe",
        "max_error_rate": "0.1",
        "max_indel_rate": "0.03",
        "max_length": None,
        "mean_quality": "25",
        "min_length": "20"
    }


def test_calculate_cache_hash(trim_parameters):
    hashed = virtool.caches.db.calculate_cache_hash(trim_parameters)
    assert hashed == "68b60be51a667882d3aaa02a93259dd526e9c990"


@pytest.mark.parametrize("paired", [True, False], ids=["paired", "unpaired"])
def test_create(paired, dbs, test_random_alphanumeric, create_result, trim_parameters):
    """
    Test that the function works with default keyword arguments and when `paired` is either `True` or `False`.

    """
    cache_id = virtool.caches.db.create(dbs, "foo", trim_parameters, paired)

    assert dbs.caches.find_one() == {
        **create_result,
        "_id": test_random_alphanumeric.last_choice,
        "paired": paired
    }

    assert cache_id == test_random_alphanumeric.last_choice


def test_create_legacy(dbs, test_random_alphanumeric, create_result, trim_parameters):
    """
    Test that the function works when the `legacy` keyword argument is `True` instead of the default `False`.

    """
    cache_id = virtool.caches.db.create(dbs, "foo", trim_parameters, False, legacy=True)

    assert dbs.caches.find_one() == {
        **create_result,
        "_id": test_random_alphanumeric.last_choice,
        "legacy": True
    }

    assert cache_id == test_random_alphanumeric.last_choice


def test_create_program(dbs, test_random_alphanumeric, create_result, trim_parameters):
    """
    Test that the function works with a non-default trimming program keyword argument
    (trimmomatic-0.2.3 instead of skewer-0.2.2).

    """
    cache_id = virtool.caches.db.create(dbs, "foo", trim_parameters, False, program="trimmomatic-0.2.3")

    assert dbs.caches.find_one({"_id": test_random_alphanumeric.last_choice}) == {
        **create_result,
        "_id": test_random_alphanumeric.last_choice,
        "program": "trimmomatic-0.2.3"
    }

    assert cache_id == test_random_alphanumeric.last_choice


def test_create_duplicate(dbs, test_random_alphanumeric, create_result, trim_parameters):
    """
    Test that the function handles duplicate document ids smoothly. The function should retry with a new id.

    """
    dbs.caches.insert_one({"_id": test_random_alphanumeric.next_choice[:8].lower()})

    cache_id = virtool.caches.db.create(dbs, "foo", trim_parameters, False)

    assert cache_id == "u3cuwaoq"

    assert dbs.caches.find_one({"_id": test_random_alphanumeric.last_choice}) == {
        **create_result,
        "_id": test_random_alphanumeric.last_choice
    }


@pytest.mark.parametrize("exists", [True, False])
async def test_get(exists, dbi):
    """
    Test that the function returns a cache document when it exists and returns `None` when it does not.

    """
    if exists:
        await dbi.caches.insert_one({"_id": "foo"})

    result = await virtool.caches.db.get(dbi, "foo")

    if exists:
        assert result == {"id": "foo"}
        return

    assert result is None


@pytest.mark.parametrize("exception", [False, True])
async def test_remove(exception, dbi):
    app = {
        "db": dbi,
        "run_in_thread": make_mocked_coro(raise_exception=FileNotFoundError) if exception else make_mocked_coro(),
        "settings": {
            "data_path": "/foo"
        }
    }

    await dbi.caches.insert_one({"_id": "baz"})

    await virtool.caches.db.remove(app, "baz")

    assert await dbi.caches.count() == 0

    app["run_in_thread"].assert_called_with(
        virtool.utils.rm,
        "/foo/caches/baz",
        True
    )
