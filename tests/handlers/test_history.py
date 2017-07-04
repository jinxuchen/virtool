import pytest

import virtool.virus


class TestFind:

    async def test(self, test_db, do_get, test_changes):
        """
        Test that a list of processed change documents are returned with a ``200`` status.
         
        """
        test_db.history.insert_many(test_changes)

        resp = await do_get("/api/history")

        assert resp.status == 200

        assert await resp.json() == [
            {
                "description": ["Edited virus", "Prunus virus E"],
                "id": "6116cba1.1",
                "index": {
                    "id": "unbuilt",
                    "version": "unbuilt"
                },
                "method_name": "edit",
                "timestamp": "2017-10-06T20:00:00Z",
                "user": {
                    "id": "test"
                },
                "virus": {
                    "id": "6116cba1",
                    "name": "Prunus virus F",
                    "version": 1
                }
            },
            {
                "description": ["Edited virus", "Prunus virus E"],
                "id": "foobar.1",
                "index": {
                    "id": "unbuilt",
                    "version": "unbuilt"
                },
                "method_name": "edit",
                "timestamp": "2017-10-06T20:00:00Z",
                "user": {
                    "id": "test"
                },
                "virus": {
                    "id": "6116cba1",
                    "name": "Prunus virus F",
                    "version": 1
                }
            },
            {
                "description": ["Edited virus", "Prunus virus E"],
                "id": "foobar.2",
                "index": {
                    "id": "unbuilt",
                    "version": "unbuilt"
                },
                "method_name": "edit",
                "timestamp": "2017-10-06T20:00:00Z",
                "user": {
                    "id": "test"
                },
                "virus": {
                    "id": "6116cba1",
                    "name": "Prunus virus F",
                    "version": 1
                }
            }
        ]
        

class TestGet:

    async def test(self, test_db, do_get, test_changes):
        """
        Test that a specific history change can be retrieved by its change_id.
         
        """
        test_db.history.insert_many(test_changes)

        resp = await do_get("/api/history/6116cba1.1")

        assert resp.status == 200

        assert await resp.json() == {
            "description": ["Edited virus", "Prunus virus E"],
            "diff": [
                ["change", "abbreviation", ["PVF", ""]],
                ["change", "name", ["Prunus virus F", "Prunus virus E"]],
                ["change", "version", [0, 1]]
            ],
            "id": "6116cba1.1",
            "index": {
                "id": "unbuilt",
                "version": "unbuilt"
            },
            "method_name": "edit",
            "timestamp": "2017-10-06T20:00:00Z",
            "user": {
                "id": "test"
            },
            "virus": {
                "id": "6116cba1",
                "name": "Prunus virus F",
                "version": 1
            }
        }

    async def test_not_found(self, do_get):
        """
        Test that a specific history change can be retrieved by its change_id.

        """
        resp = await do_get("/api/history/foobar.1")

        assert resp.status == 404

        assert await resp.json() == {
            "message": "Not found"
        }


class TestRemove:

    @pytest.mark.parametrize("remove", [True, False])
    async def test(self, remove, test_motor, do_delete, setup_test_history):
        """
        Test that a valid request results in a reversion and a ``204`` response.
         
        """
        expected = await setup_test_history(remove=remove)

        await do_delete("/api/history/6116cba1.2")

        joined = await virtool.virus.join(test_motor, expected["_id"])

        assert joined == expected

    async def test_not_found(self, do_delete):
        """
        Test that a request for a non-existent ``change_id`` results in a ``404`` response.
         
        """
        resp = await do_delete("/api/history/6116cba1.1")

        assert resp.status == 404

        assert await resp.json() == {
            "message": "Not found"
        }
