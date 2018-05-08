from copy import deepcopy

import pytest
from aiohttp.test_utils import make_mocked_coro

import virtool.db.otus
import virtool.otus


@pytest.mark.parametrize("find", [None, "tobacco"])
@pytest.mark.parametrize("verified", [None, True, False])
@pytest.mark.parametrize("names", [None, True, False])
async def test_find(find, verified, names, mocker, spawn_client, test_otu):
    """


    """
    client = await spawn_client(authorize=True)

    result = {
        "documents": [test_otu]
    }

    m = mocker.patch("virtool.db.otus.find", make_mocked_coro(result))

    params = {}

    if find is not None:
        params["find"] = find

    for key, value in [("names", names), ("verified", verified)]:
        if value is not None:
            params[key] = str(value)

    resp = await client.get("/api/otus", params=params)

    assert resp.status == 200

    assert await resp.json() == result

    m.assert_called_with(
        client.db,
        names or False,
        find,
        mocker.ANY,
        verified
    )


@pytest.mark.parametrize("exists", [True, False])
async def test_get(exists, spawn_client, resp_is, test_otu, test_sequence):
    """
    Test that a valid request returns a complete otu document.

    """
    client = await spawn_client(authorize=True)

    if exists:
        await client.db.otus.insert_one(test_otu)
        await client.db.sequences.insert_one(test_sequence)

    resp = await client.get("/api/otus/{}".format(test_otu["_id"]))

    if exists:
        assert resp.status == 200

        assert await resp.json() == {
            "abbreviation": "PVF",
            "imported": True,
            "last_indexed_version": 0,
            "verified": False,
            "most_recent_change": None,
            "name": "Prunus virus F",
            "version": 0,
            "id": "6116cba1",
            "schema": [],
            "isolates": [
                {
                    "id": "cab8b360",
                    "source_type": "isolate",
                    "source_name": "8816-v2",
                    "default": True,
                    "sequences": [
                        {
                            "id": "KX269872",
                            "definition": "Prunus virus F isolate 8816-s2 "
                            "segment RNA2 polyprotein 2 gene, complete cds.",
                            "host": "sweet cherry",
                            "sequence": "TGTTTAAGAGATTAAACAACCGCTTTC",
                            "segment": None
                        }
                    ]
                }
            ],
            "issues": None,
            "ref": {
                "id": "hxn167"
            }
        }
    else:
        assert await resp_is.not_found(resp)


class TestCreate:

    @pytest.mark.parametrize("abbreviation", [None, "", "TMV"])
    async def test(self, abbreviation, mocker, spawn_client, test_merged_otu):
        """
        Test that a valid request results in the creation of a otu document and a ``201`` response.

        """
        client = await spawn_client(authorize=True)

        # Pass ref exists check.
        mocker.patch("virtool.db.utils.id_exists", make_mocked_coro(True))

        # Pass name and abbreviation check.
        m_check_name_and_abbreviation = mocker.patch(
            "virtool.db.otus.check_name_and_abbreviation",
            make_mocked_coro(False)
        )

        m_add_history = mocker.patch("virtool.db.history.add", make_mocked_coro({"_id": "change.1"}))

        #
        m_compose = mocker.patch("virtool.history.compose_create_description", return_value="Test description")

        m_create = mocker.patch("virtool.db.otus.create", make_mocked_coro(test_merged_otu))

        data = {
            "name": "Tobacco mosaic virus"
        }

        if abbreviation is not None:
            data["abbreviation"] = abbreviation

        resp = await client.post("/api/refs/foo/otus", data)

        assert resp.status == 201

        assert resp.headers["Location"] == "/api/otus/" + test_merged_otu["_id"]

        # Abbreviation defaults to empty string for OTU creation.
        m_check_name_and_abbreviation.assert_called_with(
            client.db,
            "foo",
            "Tobacco mosaic virus",
            abbreviation or ""
        )

        m_create.assert_called_with(
            client.db,
            "foo",
            "Tobacco mosaic virus",
            abbreviation or ""
        )

        m_compose.assert_called_with(test_merged_otu)

        test_merged_otu["abbreviation"] = "PVF"

        m_add_history.assert_called_with(
            client.db,
            "create",
            None,
            test_merged_otu,
            "Test description",
            "test"
        )

    async def test_invalid_input(self, spawn_client, resp_is):
        """
        Test that invalid input results in a ``422`` response with error data.

        """
        client = await spawn_client(authorize=True)

        data = {
            "otu_name": "Tobacco mosaic otu",
            "abbreviation": 123
        }

        resp = await client.post("/api/refs/foo/otus", data)

        assert resp.status == 422

        assert await resp_is.invalid_input(resp, {
            "otu_name": ["unknown field"],
            "abbreviation": ["must be of string type"],
            "name": ["required field"]
        })

    @pytest.mark.parametrize("message", [
        False,
        "Name already exists",
        "Abbreviation already exists",
        "Name and abbreviation already exist"
    ])
    async def test_field_exists(self, message, mocker, spawn_client, resp_is):
        """
        Test that the request fails with ``409 Conflict`` if the requested otu name already exists.

        """
        # Pass ref exists check.
        mocker.patch("virtool.db.utils.id_exists", make_mocked_coro(True))

        # Pass name and abbreviation check.
        m_check_name_and_abbreviation = mocker.patch(
            "virtool.db.otus.check_name_and_abbreviation",
            make_mocked_coro(message)
        )

        client = await spawn_client(authorize=True)

        data = {
            "name": "Tobacco mosaic virus",
            "abbreviation": "TMV"
        }

        resp = await client.post("/api/refs/foo/otus", data)

        # Abbreviation defaults to empty string for OTU creation.
        m_check_name_and_abbreviation.assert_called_with(
            client.db,
            "foo",
            "Tobacco mosaic virus",
            "TMV"
        )

        if message:
            assert await resp_is.conflict(resp, message)

        else:
            assert resp.status == 201


class TestEdit:

    @pytest.mark.parametrize("data, existing_abbreviation, description", [
        # Name, ONLY.
        (
            {"name": "Tobacco mosaic otu"},
            "TMV",
            "Changed name to Tobacco mosaic otu"
        ),
        # Name and abbreviation, BOTH CHANGE.
        (
            {"name": "Tobacco mosaic otu", "abbreviation": "TMV"},
            "PVF",
            "Changed name to Tobacco mosaic otu and changed abbreviation to TMV"
        ),
        # Name and abbreviation, NO NAME CHANGE because old is same as new.
        (
            {"name": "Prunus virus F", "abbreviation": "TMV"},
            "PVF",
            "Changed abbreviation to TMV"
        ),
        # Name and abbreviation, NO ABBR CHANGE because old is same as new.
        (
            {"name": "Tobacco mosaic otu", "abbreviation": "TMV"},
            "TMV",
            "Changed name to Tobacco mosaic otu"
        ),
        # Name and abbreviation, ABBR REMOVED because old is "TMV" and new is "".
        (
            {"name": "Tobacco mosaic otu", "abbreviation": ""},
            "TMV",
            "Changed name to Tobacco mosaic otu and removed abbreviation TMV"
        ),
        # Name and abbreviation, ABBR ADDED because old is "" and new is "TMV".
        (
            {"name": "Tobacco mosaic otu", "abbreviation": "TMV"},
            "",
            "Changed name to Tobacco mosaic otu and added abbreviation TMV"
        ),
        # Abbreviation, ONLY.
        (
            {"abbreviation": "TMV"},
            "PVF",
            "Changed abbreviation to TMV"
        ),
        # Abbreviation, ONLY because old name is same as new.
        (
            {"name": "Prunus virus F", "abbreviation": "TMV"},
            "PVF",
            "Changed abbreviation to TMV"
        ),
        # Abbreviation, ADDED.
        (
            {"abbreviation": "TMV"},
            "",
            "Added abbreviation TMV"
        ),
        # Abbreviation, REMOVED.
        (
            {"abbreviation": ""},
            "TMV",
            "Removed abbreviation TMV"
        )
    ])
    async def test(self, data, existing_abbreviation, description, spawn_client, test_otu, test_add_history,
                   test_dispatch):
        """
        Test that changing the name and abbreviation results in changes to the otu document and a new change
        document in history. The that change both fields or one or the other results in the correct changes and
        history record.

        """
        client = await spawn_client(authorize=True, permissions=["modify_otu"])

        test_otu["abbreviation"] = existing_abbreviation

        await client.db.otus.insert_one(test_otu)

        resp = await client.patch("/api/otus/6116cba1", data)

        assert resp.status == 200

        expected = {
            "id": "6116cba1",
            "abbreviation": existing_abbreviation,
            "imported": True,
            "isolates": [
                {
                    "default": True,
                    "id": "cab8b360",
                    "sequences": [],
                    "source_name": "8816-v2",
                    "source_type": "isolate"
                }
            ],
            "last_indexed_version": 0,
            "verified": False,
            "most_recent_change": None,
            "name": "Prunus virus F",
            "version": 1,
            "schema": [],
            "issues": None,
            "ref": {
                "id": "hxn167"
            }
        }

        old = deepcopy(expected)

        expected.update(data)

        assert await resp.json() == expected

        expected.update({
            "lower_name": expected["name"].lower(),
            "_id": expected.pop("id")
        })

        expected.pop("most_recent_change")
        expected.pop("issues")

        for isolate in expected["isolates"]:
            isolate.pop("sequences")

        assert await client.db.otus.find_one() == expected

        expected_dispatch = {
            "id": "6116cba1",
            "name": "Prunus virus F",
            "abbreviation": existing_abbreviation,
            "verified": False,
            "version": 1
        }

        expected_dispatch.update(data)

        assert test_dispatch.stub.call_args[0] == (
            "otus",
            "update",
            expected_dispatch
        )

        old.pop("issues")

        old.update({
            "_id": old.pop("id"),
            "lower_name": old["name"].lower(),
            "version": 0
        })

        old.pop("most_recent_change")

        for isolate in expected["isolates"]:
            isolate["sequences"] = []

        assert test_add_history.call_args[0][1:] == (
            "edit",
            old,
            expected,
            description,
            "test"
        )

    async def test_invalid_input(self, spawn_client, resp_is):
        """
        Test that invalid input results in a ``422`` response with error data.

        """
        client = await spawn_client(authorize=True, permissions=["modify_otu"])

        data = {
            "otu_name": "Tobacco mosaic otu",
            "abbreviation": 123
        }

        resp = await client.patch("/api/otus/test", data)

        assert resp.status == 422

        assert await resp_is.invalid_input(resp, {
            "otu_name": ["unknown field"],
            "abbreviation": ["must be of string type"]
        })

    async def test_name_exists(self, spawn_client):
        """
        Test that the request fails with ``409 Conflict`` if the requested otu name already exists.

        """
        client = await spawn_client(authorize=True, permissions=["modify_otu"])

        await client.db.otus.insert_many([
            {
                "_id": "test",
                "name": "Prunus virus F",
                "lower_name": "Prunus virus F",
                "isolates": [],
                "ref": {
                    "id": "foo"
                }
            },
            {
                "_id": "conflict",
                "name": "Tobacco mosaic otu",
                "lower_name": "tobacco mosaic otu",
                "isolates": [],
                "ref": {
                    "id": "foo"
                }
            }
        ])

        data = {
            "name": "Tobacco mosaic otu",
            "abbreviation": "TMV"
        }

        resp = await client.patch("/api/otus/test", data)

        assert resp.status == 409

        assert await resp.json() == {
            "message": "Name already exists"
        }

    async def test_abbreviation_exists(self, spawn_client):
        """
        Test that the request fails with ``409 Conflict`` if the requested abbreviation already exists.

        """
        client = await spawn_client(authorize=True, permissions=["modify_otu"])

        await client.db.otus.insert_many([
            {
                "_id": "test",
                "name": "Prunus virus F",
                "lower_name": "Prunus virus F",
                "abbreviation": "PVF",
                "isolates": [],
                "ref": {
                    "id": "foo"
                }
            },
            {
                "_id": "conflict",
                "name": "Tobacco mosaic otu",
                "lower_name": "tobacco mosaic otu",
                "abbreviation": "TMV",
                "isolates": [],
                "ref": {
                    "id": "foo"
                }
            }
        ])

        data = {
            "abbreviation": "TMV"
        }

        resp = await client.patch("/api/otus/test", data)

        assert resp.status == 409

        assert await resp.json() == {
            "message": "Abbreviation already exists"
        }

    async def test_both_exist(self, spawn_client):
        """
        Test that the request fails with ``409 Conflict`` if the requested name and abbreviation already exist.

        """
        client = await spawn_client(authorize=True, permissions=["modify_otu"])

        await client.db.otus.insert_many([
            {
                "_id": "test",
                "name": "Prunus virus F",
                "lower_name": "Prunus virus F",
                "abbreviation": "PVF",
                "isolates": [],
                "ref": {
                    "id": "foo"
                }
            },
            {
                "_id": "conflict",
                "name": "Tobacco mosaic otu",
                "lower_name": "tobacco mosaic otu",
                "abbreviation": "TMV",
                "isolates": [],
                "ref": {
                    "id": "foo"
                }
            }
        ])

        data = {
            "name": "Tobacco mosaic otu",
            "abbreviation": "TMV"
        }

        resp = await client.patch("/api/otus/test", data)

        assert resp.status == 409

        assert await resp.json() == {
            "message": "Name and abbreviation already exist"
        }

    @pytest.mark.parametrize("old_name,old_abbr,data", [
        ("Tobacco mosaic otu", "TMV", {"name": "Tobacco mosaic otu", "abbreviation": "TMV"}),
        ("Tobacco mosaic otu", "TMV", {"name": "Tobacco mosaic otu"}),
        ("Tobacco mosaic otu", "TMV", {"abbreviation": "TMV"})
    ])
    async def test_no_change(self, old_name, old_abbr, data, spawn_client):
        client = await spawn_client(authorize=True, permissions=["modify_otu"])

        await client.db.otus.insert_one({
            "_id": "test",
            "name": old_name,
            "lower_name": "tobacco mosaic otu",
            "abbreviation": old_abbr,
            "isolates": [],
            "ref": {
                "id": "foo"
            }
        })

        resp = await client.patch("/api/otus/test", data)

        assert resp.status == 200

        assert await resp.json() == {
            "abbreviation": "TMV",
            "id": "test",
            "isolates": [],
            "most_recent_change": None,
            "name": "Tobacco mosaic otu",
            "issues": None,
            "ref": {
                "id": "foo"
            }
        }

    async def test_not_found(self, spawn_client, resp_is):
        client = await spawn_client(authorize=True, permissions=["modify_otu"])

        data = {
            "name": "Tobacco mosaic otu",
            "abbreviation": "TMV"
        }

        resp = await client.patch("/api/otus/test", data)

        assert await resp_is.not_found(resp)


class TestRemove:

    @pytest.mark.parametrize("abbreviation,description", [
        ("", "Removed Prunus virus F"),
        ("PVF", "Removed Prunus virus F (PVF)")
    ])
    async def test(self, abbreviation, description, spawn_client, test_otu, test_add_history, test_dispatch):
        """
        Test that an existing otu can be removed.

        """
        client = await spawn_client(authorize=True, permissions=["modify_otu"])

        test_otu["abbreviation"] = abbreviation

        await client.db.otus.insert_one(test_otu)

        old = await client.db.otus.find_one("6116cba1")

        assert old

        resp = await client.delete("/api/otus/6116cba1")

        assert resp.status == 204

        assert await client.db.otus.find({"_id": "6116cba1"}).count() == 0

        old["isolates"][0]["sequences"] = []

        assert test_add_history.call_args[0][1:] == (
            "remove",
            old,
            None,
            description,
            "test"
        )

        assert test_dispatch.stub.call_args[0] == (
            "otus",
            "remove",
            ["6116cba1"]
        )

    async def test_not_found(self, spawn_client, resp_is):
        """
        Test that attempting to remove a non-existent otu results in a ``404`` response.

        """
        client = await spawn_client(authorize=True, permissions=["modify_otu"])

        resp = await client.delete("/api/otus/6116cba1")

        assert await resp_is.not_found(resp)


@pytest.mark.parametrize("exists", [True, False])
async def test_list_isolates(exists, spawn_client, resp_is, test_otu):
    """
    Test the isolates are properly listed and formatted for an existing otu.

    """
    client = await spawn_client(authorize=True)

    if exists:
        test_otu["isolates"].append({
            "default": False,
            "source_type": "isolate",
            "source_name": "7865",
            "id": "bcb9b352"
        })

        await client.db.otus.insert_one(test_otu)

    resp = await client.get("/api/otus/6116cba1/isolates")

    if exists:
        assert resp.status == 200

        assert await resp.json() == [
            {
                "default": True,
                "source_type": "isolate",
                "source_name": "8816-v2",
                "id": "cab8b360",
                "sequences": []
            },
            {
                "default": False,
                "source_type": "isolate",
                "source_name": "7865",
                "id": "bcb9b352",
                "sequences": []
            }
        ]

    else:
        assert await resp_is.not_found(resp)


class TestGetIsolate:

    async def test(self, spawn_client, test_otu, test_sequence):
        """
        Test that an existing isolate is successfully returned.

        """
        client = await spawn_client(authorize=True)

        await client.db.otus.insert_one(test_otu)
        await client.db.sequences.insert_one(test_sequence)

        resp = await client.get("/api/otus/6116cba1/isolates/cab8b360")

        assert resp.status == 200

        test_sequence["id"] = test_sequence.pop("_id")
        del test_sequence["otu_id"]
        del test_sequence["isolate_id"]

        assert await resp.json() == {
            "default": True,
            "source_type": "isolate",
            "source_name": "8816-v2",
            "id": "cab8b360",
            "sequences": [test_sequence]
        }

    @pytest.mark.parametrize("otu_id,isolate_id", [
        ("foobar", "cab8b360"),
        ("6116cba1", "foobar"),
        ("6116cba1", "cab8b360")
    ])
    async def test_not_found(self, otu_id, isolate_id, spawn_client, resp_is):
        """
        Test that a ``404`` response results for a non-existent otu and/or isolate.

        """
        client = await spawn_client(authorize=True)

        resp = await client.get("/api/otus/{}/isolates/{}".format(otu_id, isolate_id))

        assert await resp_is.not_found(resp)


class TestAddIsolate:

    async def test_is_default(self, mocker, spawn_client, test_otu, test_add_history, test_dispatch):
        """
        Test that a new default isolate can be added, setting ``default`` to ``False`` on all other isolates in the
        process.

        """
        client = await spawn_client(authorize=True, permissions=["modify_otu"])

        client.app["settings"]["restrict_source_types"] = True
        client.app["settings"]["allowed_source_types"] = ["isolate"]

        await client.db.otus.insert_one(test_otu)

        data = {
            "source_name": "b",
            "source_type": "isolate",
            "default": True
        }

        mocker.patch("virtool.db.otus.get_new_isolate_id", make_mocked_coro("test"))

        resp = await client.post("/api/otus/6116cba1/isolates", data)

        assert resp.status == 201

        assert resp.headers["Location"] == "/api/otus/6116cba1/isolates/test"

        assert await resp.json() == {
            "id": "test",
            "source_type": "isolate",
            "source_name": "b",
            "default": True,
            "sequences": []
        }

        new = await client.db.otus.find_one("6116cba1")

        assert new["isolates"] == [
            {
                "id": "cab8b360",
                "default": False,
                "source_type": "isolate",
                "source_name": "8816-v2"
            },
            {
                "id": "test",
                "source_name": "b",
                "source_type": "isolate",
                "default": True
            }
        ]

        for isolate in new["isolates"]:
            isolate["sequences"] = []

        test_otu["isolates"][0]["sequences"] = []

        assert test_add_history.call_args[0][1:] == (
            "add_isolate",
            test_otu,
            new,
            "Added Isolate b as default",
            "test"
        )

        assert test_dispatch.stub.call_args[0] == (
            "otus",
            "update",
            {
                "id": "6116cba1",
                "name": "Prunus virus F",
                "abbreviation": "PVF",
                "verified": False,
                "version": 1
            }
        )

    async def test_not_default(self, monkeypatch, spawn_client, test_otu, test_add_history, test_dispatch):
        """
        Test that a non-default isolate can be properly added

        """
        client = await spawn_client(authorize=True, permissions=["modify_otu"])

        client.app["settings"]["restrict_source_types"] = True
        client.app["settings"]["allowed_source_types"] = ["isolate"]

        await client.db.otus.insert_one(test_otu)

        data = {
            "source_name": "b",
            "source_type": "isolate",
            "default": False
        }

        monkeypatch.setattr("virtool.db.otus.get_new_isolate_id", make_mocked_coro("test"))

        resp = await client.post("/api/otus/6116cba1/isolates", data)

        assert resp.status == 201

        assert resp.headers["Location"] == "/api/otus/6116cba1/isolates/test"

        assert await resp.json() == {
            "source_name": "b",
            "source_type": "isolate",
            "id": "test",
            "default": False,
            "sequences": []
        }

        new = await client.db.otus.find_one("6116cba1")

        assert new["isolates"] == [
            {
                "id": "cab8b360",
                "source_type": "isolate",
                "source_name": "8816-v2",
                "default": True
            },
            {
                "id": "test",
                "source_name": "b",
                "source_type": "isolate",
                "default": False
            }
        ]

        for isolate in new["isolates"]:
            isolate["sequences"] = []

        test_otu["isolates"][0]["sequences"] = []

        assert test_add_history.call_args[0][1:] == (
            "add_isolate",
            test_otu,
            new,
            "Added Isolate b",
            "test"
        )

        assert test_dispatch.stub.call_args[0] == (
            "otus",
            "update",
            {
                "id": "6116cba1",
                "name": "Prunus virus F",
                "abbreviation": "PVF",
                "verified": False,
                "version": 1
            }
        )

    async def test_first(self, monkeypatch, spawn_client, test_otu, test_add_history, test_dispatch):
        """
        Test that the first isolate for a otu is set as the ``default`` otu even if ``default`` is set to ``False``
        in the POST input.

        """
        client = await spawn_client(authorize=True, permissions=["modify_otu"])

        client.app["settings"]["restrict_source_types"] = True
        client.app["settings"]["allowed_source_types"] = ["isolate"]

        test_otu["isolates"] = []

        await client.db.otus.insert_one(test_otu)

        data = {
            "source_name": "b",
            "source_type": "isolate",
            "default": False
        }

        monkeypatch.setattr("virtool.db.otus.get_new_isolate_id", make_mocked_coro("test"))

        resp = await client.post("/api/otus/6116cba1/isolates", data)

        assert resp.status == 201

        assert resp.headers["Location"] == "/api/otus/6116cba1/isolates/test"

        assert await resp.json() == {
            "source_name": "b",
            "source_type": "isolate",
            "id": "test",
            "default": True,
            "sequences": []
        }

        new = await client.db.otus.find_one("6116cba1")

        assert new["isolates"] == [{
            "id": "test",
            "default": True,
            "source_type": "isolate",
            "source_name": "b"
        }]

        new["isolates"][0]["sequences"] = []

        assert test_add_history.call_args[0][1:] == (
            "add_isolate",
            test_otu,
            new,
            "Added Isolate b as default",
            "test"
        )

        assert test_dispatch.stub.call_args[0] == (
            "otus",
            "update",
            {
                "id": "6116cba1",
                "name": "Prunus virus F",
                "abbreviation": "PVF",
                "verified": False,
                "version": 1
            }
        )

    async def test_force_case(self, monkeypatch, spawn_client, test_otu, test_dispatch):
        """
        Test that the ``source_type`` value is forced to lower case.

        """
        client = await spawn_client(authorize=True, permissions=["modify_otu"])

        client.app["settings"]["restrict_source_types"] = True
        client.app["settings"]["allowed_source_types"] = ["isolate"]

        await client.db.otus.insert_one(test_otu)

        data = {
            "source_name": "Beta",
            "source_type": "Isolate",
            "default": False
        }

        monkeypatch.setattr("virtool.db.otus.get_new_isolate_id", make_mocked_coro("test"))

        resp = await client.post("/api/otus/6116cba1/isolates", data)

        assert resp.status == 201

        assert resp.headers["Location"] == "/api/otus/6116cba1/isolates/test"

        assert await resp.json() == {
            "source_name": "Beta",
            "source_type": "isolate",
            "id": "test",
            "default": False,
            "sequences": []
        }

        document = await client.db.otus.find_one("6116cba1")

        assert document["isolates"] == [
            {
                "id": "cab8b360",
                "default": True,
                "source_type": "isolate",
                "source_name": "8816-v2"
            },
            {
                "id": "test",
                "source_name": "Beta",
                "source_type": "isolate",
                "default": False
            }
        ]

        assert test_dispatch.stub.call_args[0] == (
            "otus",
            "update",
            {
                "id": "6116cba1",
                "name": "Prunus virus F",
                "abbreviation": "PVF",
                "verified": False,
                "version": 1
            }
        )

    async def test_empty(self, mocker, spawn_client, test_otu, test_dispatch):
        """
        Test that an isolate can be added without any POST input. The resulting document should contain the defined
        default values.

        """
        client = await spawn_client(authorize=True, permissions=["modify_otu"])

        await client.db.otus.insert_one(test_otu)

        mocker.patch("virtool.db.otus.get_new_isolate_id", make_mocked_coro("test"))

        resp = await client.post("/api/otus/6116cba1/isolates", {})

        assert resp.status == 201

        assert resp.headers["Location"] == "/api/otus/6116cba1/isolates/test"

        assert await resp.json() == {
            "id": "test",
            "source_name": "",
            "source_type": "",
            "default": False,
            "sequences": []
        }

        assert (await client.db.otus.find_one("6116cba1", ["isolates"]))["isolates"] == [
            {
                "id": "cab8b360",
                "default": True,
                "source_type": "isolate",
                "source_name": "8816-v2"
            },
            {
                "id": "test",
                "source_name": "",
                "source_type": "",
                "default": False
            }
        ]

        assert test_dispatch.stub.call_args[0] == (
            "otus",
            "update",
            {
                "id": "6116cba1",
                "name": "Prunus virus F",
                "abbreviation": "PVF",
                "verified": False,
                "version": 1
            }
        )

    async def test_not_found(self, spawn_client, resp_is):
        client = await spawn_client(authorize=True, permissions=["modify_otu"])

        data = {
            "source_name": "Beta",
            "source_type": "Isolate",
            "default": False
        }

        resp = await client.post("/api/otus/6116cba1/isolates", data)

        assert await resp_is.not_found(resp)


class TestEditIsolate:

    @pytest.mark.parametrize("data,description", [
        ({"source_type": "variant"}, "Renamed Isolate b to Variant b"),
        ({"source_type": "variant"}, "Renamed Isolate b to Variant b"),
        ({"source_type": "variant", "source_name": "A"}, "Renamed Isolate b to Variant A"),
        ({"source_name": "A"}, "Renamed Isolate b to Isolate A")
    ])
    async def test(self, data, description, spawn_client, test_otu, test_add_history, test_dispatch):
        """
        Test that a change to the isolate name results in the correct changes, history, and response.

        """
        client = await spawn_client(authorize=True, permissions=["modify_otu"])

        test_otu["isolates"].append({
            "id": "test",
            "source_name": "b",
            "source_type": "isolate",
            "default": False
        })

        await client.db.otus.insert_one(test_otu)

        resp = await client.patch("/api/otus/6116cba1/isolates/test", data)

        assert resp.status == 200

        expected = dict(test_otu["isolates"][1])

        expected.update(data)

        assert await resp.json() == dict(expected, sequences=[])

        new = await client.db.otus.find_one("6116cba1")

        assert new["isolates"] == [
            {
                "id": "cab8b360",
                "default": True,
                "source_type": "isolate",
                "source_name": "8816-v2"
            },
            expected
        ]

        for joined in (test_otu, new):
            for isolate in joined["isolates"]:
                isolate["sequences"] = []

        assert test_add_history.call_args[0][1:] == (
            "edit_isolate",
            test_otu,
            new,
            description,
            "test"
        )

        assert test_dispatch.stub.call_args[0] == (
            "otus",
            "update",
            {
                "id": "6116cba1",
                "name": "Prunus virus F",
                "abbreviation": "PVF",
                "verified": False,
                "version": 1
            }
        )

    async def test_force_case(self, monkeypatch, spawn_client, test_otu, test_dispatch):
        """
        Test that the ``source_type`` value is forced to lower case.

        """
        client = await spawn_client(authorize=True, permissions=["modify_otu"])

        await client.db.otus.insert_one(test_otu)

        data = {
            "source_type": "Variant",
        }

        monkeypatch.setattr("virtool.db.otus.get_new_isolate_id", make_mocked_coro("test"))

        resp = await client.patch("/api/otus/6116cba1/isolates/cab8b360", data)

        assert resp.status == 200

        expected = {
            "id": "cab8b360",
            "default": True,
            "source_type": "variant",
            "source_name": "8816-v2",
            "sequences": []
        }

        assert await resp.json() == expected

        del expected["sequences"]

        assert (await client.db.otus.find_one("6116cba1", ["isolates"]))["isolates"] == [expected]

        assert test_dispatch.stub.call_args[0] == (
            "otus",
            "update",
            {
                "id": "6116cba1",
                "name": "Prunus virus F",
                "abbreviation": "PVF",
                "verified": False,
                "version": 1
            }
        )

    async def test_invalid_input(self, spawn_client, test_otu, resp_is):
        """
        Test that invalid input results in a ``422`` response and a list of errors.

        """
        client = await spawn_client(authorize=True, permissions=["modify_otu"])

        await client.db.otus.insert_one(test_otu)

        data = {
            "source_type": {"key": "variant"},
            "source_name": "A"
        }

        resp = await client.patch("/api/otus/6116cba1/isolates/cab8b360", data)

        assert await resp_is.invalid_input(resp, {
            "source_type": ["must be of string type"]
        })

    @pytest.mark.parametrize("otu_id,isolate_id", [
        ("6116cba1", "test"),
        ("test", "cab8b360"),
        ("test", "test")
    ])
    async def test_not_found(self, otu_id, isolate_id, spawn_client, test_otu, resp_is):
        """
        Test that a request for a non-existent otu or isolate results in a ``404`` response.

        """
        client = await spawn_client(authorize=True, permissions=["modify_otu"])

        await client.db.otus.insert_one(test_otu)

        data = {
            "source_type": "variant",
            "source_name": "A"
        }

        resp = await client.patch("/api/otus/{}/isolates/{}".format(otu_id, isolate_id), data)

        assert await resp_is.not_found(resp)


class TestSetAsDefault:

    async def test(self, spawn_client, test_otu, test_add_history, test_dispatch):
        """
        Test changing the default isolate results in the correct changes, history, and response.

        """
        client = await spawn_client(authorize=True, permissions=["modify_otu"])

        test_otu["isolates"].append({
            "id": "test",
            "source_name": "b",
            "source_type": "isolate",
            "default": False
        })

        await client.db.otus.insert_one(test_otu)

        resp = await client.put("/api/otus/6116cba1/isolates/test/default", {})

        assert resp.status == 200

        assert await resp.json() == {
            "id": "test",
            "source_type": "isolate",
            "source_name": "b",
            "default": True,
            "sequences": []
        }

        new = await virtool.db.otus.join(client.db, "6116cba1")

        assert new["isolates"] == [
            {
                "id": "cab8b360",
                "default": False,
                "source_type": "isolate",
                "source_name": "8816-v2",
                "sequences": []
            },
            {
                "id": "test",
                "source_name": "b",
                "source_type": "isolate",
                "default": True,
                "sequences": []
            }
        ]

        for joined in (test_otu, new):
            for isolate in joined["isolates"]:
                isolate["sequences"] = []

        assert test_add_history.call_args[0][1:] == (
            "set_as_default",
            test_otu,
            new,
            "Set Isolate b as default",
            "test"
        )

        assert test_dispatch.stub.call_args[0] == (
            "otus",
            "update",
            {
                "id": "6116cba1",
                "name": "Prunus virus F",
                "abbreviation": "PVF",
                "verified": False,
                "version": 1
            }
        )

    async def test_no_change(self, spawn_client, test_otu, test_add_history, test_dispatch):
        """
        Test that a call resulting in no change (calling endpoint on an already default isolate) results in no change.
        Specifically no increment in version and no dispatch.

        """
        client = await spawn_client(authorize=True, permissions=["modify_otu"])

        test_otu["isolates"].append({
            "id": "test",
            "source_name": "b",
            "source_type": "isolate",
            "default": False
        })

        await client.db.otus.insert_one(test_otu)

        resp = await client.put("/api/otus/6116cba1/isolates/cab8b360/default", {})

        assert resp.status == 200

        assert await resp.json() == {
            "id": "cab8b360",
            "default": True,
            "source_type": "isolate",
            "source_name": "8816-v2",
            "sequences": []
        }

        new = await virtool.db.otus.join(client.db, "6116cba1")

        assert new["version"] == 0

        assert new["isolates"] == [
            {
                "id": "cab8b360",
                "default": True,
                "source_type": "isolate",
                "source_name": "8816-v2",
                "sequences": []
            },
            {
                "id": "test",
                "source_name": "b",
                "source_type": "isolate",
                "default": False,
                "sequences": []
            }
        ]

        assert not test_add_history.called

        assert not test_dispatch.stub.called

    @pytest.mark.parametrize("otu_id,isolate_id", [
        ("6116cba1", "test"),
        ("test", "cab8b360"),
        ("test", "test")
    ])
    async def test_not_found(self, otu_id, isolate_id, spawn_client, test_otu, resp_is):
        """
        Test that ``404 Not found`` is returned if the otu or isolate does not exist

        """
        client = await spawn_client(authorize=True, permissions=["modify_otu"])

        await client.db.otus.insert_one(test_otu)

        resp = await client.put("/api/otus/{}/isolates/{}/default".format(otu_id, isolate_id), {})

        assert await resp_is.not_found(resp)


class TestRemoveIsolate:

    async def test(self, spawn_client, test_otu, test_sequence, test_add_history, test_dispatch):
        """
        Test that a valid request results in a ``204`` response and the isolate and sequence data is removed from the
        database.

        """
        client = await spawn_client(authorize=True, permissions=["modify_otu"])

        await client.db.otus.insert_one(test_otu)
        await client.db.sequences.insert_one(test_sequence)

        assert await client.db.otus.find({"isolates.id": "cab8b360"}).count() == 1

        resp = await client.delete("/api/otus/6116cba1/isolates/cab8b360")

        assert resp.status == 204

        assert await client.db.otus.find({"isolates.id": "cab8b360"}).count() == 0

        assert await client.db.sequences.count() == 0

        old = {
            "_id": "6116cba1",
            "abbreviation": "PVF",
            "imported": True,
            "isolates": [
                {
                    "id": "cab8b360",
                    "source_type": "isolate",
                    "source_name": "8816-v2",
                    "default": True,
                    "sequences": [
                        {
                            "_id": "KX269872",
                            "definition": "Prunus virus F isolate 8816-s2 "
                            "segment RNA2 polyprotein 2 gene, "
                            "complete cds.",
                            "host": "sweet cherry",
                            "otu_id": "6116cba1",
                            "isolate_id": "cab8b360",
                            "sequence": "TGTTTAAGAGATTAAACAACCGCTTTC",
                            "segment": None
                        }
                    ]
                }
            ],
            "schema": [],
            "last_indexed_version": 0,
            "lower_name": "prunus virus f",
            "verified": False,
            "name": "Prunus virus F",
            "version": 0,
            "ref": {
                "id": "hxn167"
            }
        }

        new = deepcopy(old)

        new.update({
            "version": 1,
            "isolates": []
        })

        assert test_add_history.call_args[0][1:] == (
            "remove_isolate",
            old,
            new,
            "Removed Isolate 8816-v2",
            "test"
        )

        assert test_dispatch.stub.call_args[0] == (
            "otus",
            "update",
            {
                "id": "6116cba1",
                "name": "Prunus virus F",
                "abbreviation": "PVF",
                "verified": False,
                "version": 1
            }
        )

    async def test_change_default(self, spawn_client, test_otu, test_sequence, test_add_history, test_dispatch):
        """
        Test that a valid request results in a ``204`` response and ``default`` status is reassigned correctly.

        """
        client = await spawn_client(authorize=True, permissions=["modify_otu"])

        test_otu["isolates"].append({
            "default": False,
            "source_type": "isolate",
            "source_name": "7865",
            "id": "bcb9b352"
        })

        await client.db.otus.insert_one(test_otu)
        await client.db.sequences.insert_one(test_sequence)

        resp = await client.delete("/api/otus/6116cba1/isolates/cab8b360")

        assert resp.status == 204

        assert await client.db.otus.find({"isolates.id": "cab8b360"}).count() == 0

        assert (await client.db.otus.find_one({"isolates.id": "bcb9b352"}, ["isolates"]))["isolates"][0]["default"]

        assert not await client.db.sequences.count()

        old = {
            "_id": "6116cba1",
            "abbreviation": "PVF",
            "imported": True,
            "isolates": [
                {
                    "id": "cab8b360",
                    "source_type": "isolate",
                    "source_name": "8816-v2",
                    "default": True,
                    "sequences": [
                        {
                            "_id": "KX269872",
                            "definition": "Prunus virus F isolate 8816-s2 "
                                          "segment RNA2 polyprotein 2 gene, "
                                          "complete cds.",
                            "host": "sweet cherry",
                            "otu_id": "6116cba1",
                            "isolate_id": "cab8b360",
                            "sequence": "TGTTTAAGAGATTAAACAACCGCTTTC",
                            "segment": None
                        }
                    ]
                },
                {
                    "default": False,
                    "source_type": "isolate",
                    "source_name": "7865",
                    "id": "bcb9b352",
                    "sequences": []
                }
            ],
            "schema": [],
            "last_indexed_version": 0,
            "lower_name": "prunus virus f",
            "verified": False,
            "name": "Prunus virus F",
            "version": 0,
            "ref": {
                "id": "hxn167"
            }
        }

        new = {
            "_id": "6116cba1",
            "abbreviation": "PVF",
            "imported": True,
            "isolates": [
                {
                    "default": True,
                    "source_type": "isolate",
                    "source_name": "7865",
                    "id": "bcb9b352",
                    "sequences": []
                }
            ],
            "last_indexed_version": 0,
            "lower_name": "prunus virus f",
            "verified": False,
            "name": "Prunus virus F",
            "schema": [],
            "version": 1,
            "ref": {
                "id": "hxn167"
            }
        }

        assert test_add_history.call_args[0][1:] == (
            "remove_isolate",
            old,
            new,
            "Removed Isolate 8816-v2 and set Isolate 7865 as default",
            "test"
        )

        assert test_dispatch.stub.call_args[0] == (
            "otus",
            "update",
            {
                "id": "6116cba1",
                "name": "Prunus virus F",
                "abbreviation": "PVF",
                "verified": False,
                "version": 1
            }
        )

    @pytest.mark.parametrize("url", ["/api/otus/foobar/isolates/cab8b360", "/api/otus/test/isolates/foobar"])
    async def test_not_found(self, url, spawn_client, test_otu, resp_is):
        """
        Test that removal fails with ``404`` if the otu does not exist.

        """
        client = await spawn_client(authorize=True, permissions=["modify_otu"])

        await client.db.otus.insert_one(test_otu)

        resp = await client.delete(url)

        assert await resp_is.not_found(resp)


class TestListSequences:

    async def test(self, spawn_client, test_otu, test_sequence):
        client = await spawn_client(authorize=True)

        await client.db.otus.insert(test_otu)
        await client.db.sequences.insert(test_sequence)

        resp = await client.get("/api/otus/6116cba1/isolates/cab8b360/sequences")

        assert resp.status == 200

        assert await resp.json() == [{
            "id": "KX269872",
            "definition": "Prunus virus F isolate 8816-s2 segment RNA2 polyprotein 2 gene, complete cds.",
            "host": "sweet cherry",
            "sequence": "TGTTTAAGAGATTAAACAACCGCTTTC",
            "segment": None
        }]

    @pytest.mark.parametrize("url", [
        "/api/otus/6116cba1/isolates/foobar/sequences",
        "/api/otus/foobar/isolates/cab8b360/sequences"
    ])
    async def test_not_found(self, url, spawn_client, resp_is):
        """
        Test that ``404`` is returned when the isolate id or sequence id do not exist.

        """
        client = await spawn_client(authorize=True)

        resp = await client.get(url)

        assert await resp_is.not_found(resp)


class TestGetSequence:

    async def test(self, spawn_client, test_otu, test_sequence):
        client = await spawn_client(authorize=True)

        await client.db.otus.insert(test_otu)
        await client.db.sequences.insert(test_sequence)

        resp = await client.get("/api/otus/6116cba1/isolates/cab8b360/sequences/KX269872")

        assert resp.status == 200

        test_sequence["id"] = test_sequence.pop("_id")

        assert await resp.json() == test_sequence

    @pytest.mark.parametrize("url", [
        "/api/otus/6116cba1/isolates/cab8b360/sequences/KX269872",
        "/api/otus/6116cba1/isolates/cab8b360/sequences/foobar",
        "/api/otus/6116cba1/isolates/foobar/sequences/KX269872",
        "/api/otus/foobar/isolates/cab8b360/sequences/KX269872",
    ])
    async def test_not_found(self, url, spawn_client, resp_is):
        client = await spawn_client(authorize=True)

        resp = await client.get(url)

        assert await resp_is.not_found(resp)


class TestCreateSequence:

    async def test(self, spawn_client, test_otu, test_add_history, test_dispatch):
        client = await spawn_client(authorize=True, permissions=["modify_otu"])

        await client.db.otus.insert_one(test_otu)

        data = {
            "id": "foobar",
            "host": "Plant",
            "sequence": "ATGCGTGTACTG",
            "definition": "A made up sequence"
        }

        resp = await client.post("/api/otus/6116cba1/isolates/cab8b360/sequences", data)

        assert resp.status == 201

        assert resp.headers["Location"] == "/api/otus/6116cba1/isolates/cab8b360/sequences/foobar"

        data.update({
            "isolate_id": "cab8b360",
            "otu_id": "6116cba1"
        })

        assert await resp.json() == {
            "id": "foobar",
            "definition": "A made up sequence",
            "otu_id": "6116cba1",
            "isolate_id": "cab8b360",
            "host": "Plant",
            "sequence": "ATGCGTGTACTG",
            "segment": None,

        }

        old = {
            "_id": "6116cba1",
            "abbreviation": "PVF",
            "imported": True,
            "schema": [],
            "isolates": [
                {
                    "default": True,
                    "id": "cab8b360",
                    "sequences": [],
                    "source_name": "8816-v2",
                    "source_type": "isolate"
                }
            ],
            "last_indexed_version": 0,
            "lower_name": "prunus virus f",
            "verified": False,
            "name": "Prunus virus F",
            "version": 0,
            "ref": {
                "id": "hxn167"
            }
        }

        new = deepcopy(old)

        new["isolates"][0]["sequences"] = [{
            "_id": "foobar",
            "definition": "A made up sequence",
            "otu_id": "6116cba1",
            "isolate_id": "cab8b360",
            "host": "Plant",
            "sequence": "ATGCGTGTACTG",
            "segment": None
        }]

        new.update({
            "verified": True,
            "version": 1
        })

        assert test_add_history.call_args[0][1:] == (
            "create_sequence",
            old,
            new,
            "Created new sequence foobar in Isolate 8816-v2",
            "test"
        )

        assert test_dispatch.stub.call_args[0] == (
            "otus",
            "update",
            {
                "id": "6116cba1",
                "abbreviation": "PVF",
                "verified": True,
                "name": "Prunus virus F",
                "version": 1
            }
        )

    async def test_exists(self, spawn_client, test_otu, test_sequence, resp_is):
        client = await spawn_client(authorize=True, permissions=["modify_otu"])

        await client.db.otus.insert(test_otu)
        await client.db.sequences.insert(test_sequence)

        resp = await client.post("/api/otus/6116cba1/isolates/cab8b360/sequences", {
            "id": "KX269872",
            "sequence": "ATGCGTGTACTG",
            "definition": "An already existing sequence"
        })

        assert await resp_is.conflict(resp, "Sequence id already exists")

    async def test_invalid_input(self, spawn_client, resp_is):
        """
        Test that invalid input results in a ``422`` response with error information.

        """
        client = await spawn_client(authorize=True, permissions=["modify_otu"])

        resp = await client.post("/api/otus/6116cba1/isolates/cab8b360/sequences", {
            "id": 2016,
            "seq": "ATGCGTGTACTG",
            "definition": "A made up sequence"
        })

        assert await resp_is.invalid_input(resp, {
            "id": ["must be of string type"],
            "sequence": ["required field"],
            "seq": ["unknown field"]
        })

    @pytest.mark.parametrize("otu_id, isolate_id", [
        ("6116cba1", "cab8b360"),
        ("6116cba1", "foobar"),
        ("foobar", "cab8b360")
    ])
    async def test_not_found(self, otu_id, isolate_id, spawn_client, resp_is):
        """
        Test that non-existent otu or isolate ids in the URL result in a ``404`` response.

        """
        client = await spawn_client(authorize=True, permissions=["modify_otu"])

        data = {
            "id": "FOOBAR",
            "host": "Plant",
            "sequence": "ATGCGTGTACTG",
            "definition": "A made up sequence"
        }

        url = "/api/otus/{}/isolates/{}/sequences".format(otu_id, isolate_id)

        resp = await client.post(url, data)

        assert await resp_is.not_found(resp, "otu or isolate not found")


class TestEditSequence:

    async def test(self, spawn_client, test_otu, test_sequence, test_add_history, test_dispatch):
        client = await spawn_client(authorize=True, permissions=["modify_otu"])

        await client.db.otus.insert(test_otu)
        await client.db.sequences.insert(test_sequence)

        data = {
            "host": "Grapevine",
            "sequence": "ATGCGTGTACTG",
            "definition": "A made up sequence"
        }

        resp = await client.patch("/api/otus/6116cba1/isolates/cab8b360/sequences/KX269872", data)

        assert resp.status == 200

        assert await resp.json() == {
            "id": "KX269872",
            "definition": "A made up sequence",
            "host": "Grapevine",
            "otu_id": "6116cba1",
            "isolate_id": "cab8b360",
            "sequence": "ATGCGTGTACTG",
            "segment": None
        }

        old = {
            "_id": "6116cba1",
            "abbreviation": "PVF",
            "imported": True,
            "isolates": [
                {
                    "default": True,
                    "id": "cab8b360",
                    "sequences": [dict(test_sequence, otu_id="6116cba1")],
                    "source_name": "8816-v2",
                    "source_type": "isolate"
                }
            ],
            "last_indexed_version": 0,
            "lower_name": "prunus virus f",
            "verified": False,
            "name": "Prunus virus F",
            "schema": [],
            "version": 0,
            "ref": {
                "id": "hxn167"
            }
        }

        new = deepcopy(old)

        new["isolates"][0]["sequences"] = [{
            "_id": "KX269872",
            "definition": "A made up sequence",
            "otu_id": "6116cba1",
            "isolate_id": "cab8b360",
            "host": "Grapevine",
            "sequence": "ATGCGTGTACTG",
            "segment": None
        }]

        new.update({
            "verified": True,
            "version": 1
        })

        assert test_add_history.call_args[0][1:] == (
            "edit_sequence",
            old,
            new,
            "Edited sequence KX269872 in Isolate 8816-v2",
            "test"
        )

        assert test_dispatch.stub.call_args[0] == (
            "otus",
            "update",
            {
                "id": "6116cba1",
                "abbreviation": "PVF",
                "verified": True,
                "name": "Prunus virus F",
                "version": 1
            }
        )

    async def test_empty_input(self, spawn_client, resp_is):
        client = await spawn_client(authorize=True, permissions=["modify_otu"])

        resp = await client.patch("/api/otus/6116cba1/isolates/cab8b360/sequences/KX269872", {})

        assert resp.status == 400

        assert await resp_is.bad_request(resp, "Empty Input")

    async def test_invalid_input(self, spawn_client, resp_is):
        client = await spawn_client(authorize=True, permissions=["modify_otu"])

        resp = await client.patch("/api/otus/6116cba1/isolates/cab8b360/sequences/KX269872", {
            "plant": "Grapevine",
            "sequence": "ATGCGTGTACTG",
            "definition": 123
        })

        assert resp.status == 422

        assert await resp_is.invalid_input(resp, {
            "definition": ["must be of string type"],
            "plant": ["unknown field"]
        })

    @pytest.mark.parametrize("foobar", ["otu_id", "isolate_id", "sequence_id"])
    async def test_not_found(self, foobar, spawn_client, test_otu, test_sequence, resp_is):
        client = await spawn_client(authorize=True, permissions=["modify_otu"])

        await client.db.otus.insert(test_otu)
        await client.db.sequences.insert(test_sequence)

        url = "/api/otus/{}/isolates/{}/sequences/{}".format(
            "foobar" if foobar == "otu_id" else "6116cba1",
            "foobar" if foobar == "isolate_id" else "cab8b360",
            "foobar" if foobar == "sequence_id" else "KX269872"
        )

        resp = await client.patch(url, {
            "host": "Grapevine",
            "sequence": "ATGCGTGTACTG",
            "definition": "A made up sequence"
        })

        assert await resp_is.not_found(resp)


class TestRemoveSequence:

    async def test(self, spawn_client, test_otu, test_sequence, test_add_history, test_dispatch):
        client = await spawn_client(authorize=True, permissions=["modify_otu"])

        await client.db.otus.insert_one(test_otu)
        await client.db.sequences.insert_one(test_sequence)

        old = await virtool.db.otus.join(client.db, test_otu["_id"])

        resp = await client.delete("/api/otus/6116cba1/isolates/cab8b360/sequences/KX269872")

        new = await virtool.db.otus.join(client.db, test_otu["_id"])

        assert test_add_history.call_args[0][1:] == (
            "remove_sequence",
            old,
            new,
            "Removed sequence KX269872 from Isolate 8816-v2",
            "test"
        )

        assert test_dispatch.stub.call_args[0] == (
            "otus",
            "update",
            {
                "id": "6116cba1",
                "abbreviation": "PVF",
                "verified": False,
                "name": "Prunus virus F",
                "version": 1
            }
        )

        assert resp.status == 204

    @pytest.mark.parametrize("otu_id,isolate_id,sequence_id", [
        ("test", "cab8b360", "KX269872"),
        ("6116cba1", "test", "KX269872"),
        ("6116cba1", "cab8b360", "test"),
        ("test", "test", "KX269872"),
        ("6116cba1", "test", "test"),
        ("test", "test", "test")
    ])
    async def test_otu_not_found(self, otu_id, isolate_id, sequence_id, test_otu, test_sequence,
                                   spawn_client, resp_is):

        client = await spawn_client(authorize=True, permissions=["modify_otu"])

        await client.db.sequences.insert_one(test_otu)
        await client.db.otus.insert_one(test_sequence)

        resp = await client.delete("/api/otus/{}/isolates/{}/sequences/{}".format(otu_id, isolate_id, sequence_id))

        await resp_is.not_found(resp)
