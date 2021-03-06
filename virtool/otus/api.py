from copy import deepcopy

from aiohttp import web

import virtool.history.db
import virtool.otus.db
import virtool.references.db
import virtool.db.utils
import virtool.history.utils
import virtool.http.routes
import virtool.otus.utils
import virtool.references.utils
import virtool.utils
import virtool.validators
from virtool.api import bad_request, insufficient_rights, json_response, no_content, not_found

SCHEMA_VALIDATOR = {
    "type": "list",
    "validator": virtool.validators.has_unique_segment_names,
    "schema": {
        "type": "dict",
        "allow_unknown": False,
        "schema": {
            "name": {"type": "string", "required": True},
            "required": {"type": "boolean", "default": True},
            "molecule": {"type": "string", "default": "", "allowed": [
                "",
                "ssDNA",
                "dsDNA",
                "ssRNA",
                "ssRNA+",
                "ssRNA-",
                "dsRNA"
            ]}
        }
    }
}

routes = virtool.http.routes.Routes()


@routes.get("/api/otus")
async def find(req):
    """
    Find otus.

    """
    db = req.app["db"]

    term = req["query"].get("find", None)
    verified = req["query"].get("verified", None)
    names = req["query"].get("names", False)

    data = await virtool.otus.db.find(
        db,
        names,
        term,
        req["query"],
        verified
    )

    return json_response(data)


@routes.get("/api/otus/{otu_id}")
async def get(req):
    """
    Get a complete otu document. Joins the otu document with its associated sequence documents.

    """
    db = req.app["db"]

    otu_id = req.match_info["otu_id"]

    complete = await virtool.otus.db.join_and_format(db, otu_id)

    if not complete:
        return not_found()

    return json_response(complete)


@routes.post("/api/refs/{ref_id}/otus", schema={
    "name": {
        "type": "string",
        "coerce": virtool.validators.strip,
        "empty": False,
        "required": True
    },
    "abbreviation": {
        "type": "string",
        "coerce": virtool.validators.strip,
        "default": ""
    },
    "schema": SCHEMA_VALIDATOR
})
async def create(req):
    """
    Add a new otu to the collection. Checks to make sure the supplied otu name and abbreviation are not already in
    use in the collection. Any errors are sent back to the client.

    """
    db = req.app["db"]
    data = req["data"]

    ref_id = req.match_info["ref_id"]

    reference = await db.references.find_one(ref_id, ["groups", "users"])

    if reference is None:
        return not_found()

    if not await virtool.references.db.check_right(req, reference, "modify_otu"):
        return insufficient_rights()

    name = data["name"].strip()
    abbreviation = data["abbreviation"].strip()

    # Check if either the name or abbreviation are already in use. Send a ``400`` if they are.
    message = await virtool.otus.db.check_name_and_abbreviation(db, ref_id, name, abbreviation)

    if message:
        return bad_request(message)

    joined = await virtool.otus.db.create(
        db,
        ref_id,
        name,
        abbreviation
    )

    description = virtool.history.utils.compose_create_description(joined)

    change = await virtool.history.db.add(
        db,
        "create",
        None,
        joined,
        description,
        req["client"].user_id
    )

    formatted = virtool.otus.utils.format_otu(joined, most_recent_change=change)

    headers = {
        "Location": "/api/otus/" + formatted["id"]
    }

    return json_response(formatted, status=201, headers=headers)


@routes.patch("/api/otus/{otu_id}", schema={
    "name": {
        "type": "string",
        "coerce": virtool.validators.strip,
        "empty": False
    },
    "abbreviation": {
        "type": "string",
        "coerce": virtool.validators.strip
    },
    "schema": SCHEMA_VALIDATOR
})
async def edit(req):
    """
    Edit an existing OTU. Checks to make sure the supplied OTU name and abbreviation are not already in use in
    the collection.

    """
    db = req.app["db"]
    data = req["data"]

    otu_id = req.match_info["otu_id"]

    # Get existing complete otu record, at the same time ensuring it exists. Send a ``404`` if not.
    old = await virtool.otus.db.join(db, otu_id)

    if not old:
        return not_found()

    ref_id = old["reference"]["id"]

    if not await virtool.references.db.check_right(req, ref_id, "modify_otu"):
        return insufficient_rights()

    name, abbreviation, schema = virtool.otus.utils.evaluate_changes(data, old)

    # Send ``200`` with the existing otu record if no change will be made.
    if name is None and abbreviation is None and schema is None:
        return json_response(await virtool.otus.db.join_and_format(db, otu_id))

    # Make sure new name or abbreviation are not already in use.
    message = await virtool.otus.db.check_name_and_abbreviation(db, ref_id, name, abbreviation)

    if message:
        return bad_request(message)

    # Update the ``modified`` and ``verified`` fields in the otu document now, because we are definitely going to
    # modify the otu.
    data["verified"] = False

    # If the name is changing, update the ``lower_name`` field in the otu document.
    if name:
        data["lower_name"] = name.lower()

    # Update the database collection.
    document = await db.otus.find_one_and_update({"_id": otu_id}, {
        "$set": data,
        "$inc": {
            "version": 1
        }
    })

    await virtool.otus.db.update_sequence_segments(db, old, document)

    new = await virtool.otus.db.join(db, otu_id, document)

    issues = await virtool.otus.db.update_verification(db, new)

    description = virtool.history.utils.compose_edit_description(name, abbreviation, old["abbreviation"], schema)

    await virtool.history.db.add(
        db,
        "edit",
        old,
        new,
        description,
        req["client"].user_id
    )

    return json_response(await virtool.otus.db.join_and_format(db, otu_id, joined=new, issues=issues))


@routes.delete("/api/otus/{otu_id}")
async def remove(req):
    """
    Remove an OTU document and its associated sequence documents.

    """
    db = req.app["db"]

    otu_id = req.match_info["otu_id"]

    document = await db.otus.find_one(otu_id, ["reference"])

    if document is None:
        return not_found()

    if not await virtool.references.db.check_right(req, document["reference"]["id"], "modify_otu"):
        return insufficient_rights()

    await virtool.otus.db.remove(
        db,
        otu_id,
        req["client"].user_id
    )

    return web.Response(status=204)


@routes.get("/api/otus/{otu_id}/isolates")
async def list_isolates(req):
    """
    Return a list of isolate records for a given otu.

    """
    db = req.app["db"]

    otu_id = req.match_info["otu_id"]

    document = await virtool.otus.db.join_and_format(db, otu_id)

    if not document:
        return not_found()

    return json_response(document["isolates"])


@routes.get("/api/otus/{otu_id}/isolates/{isolate_id}")
async def get_isolate(req):
    """
    Get a complete specific isolate sub-document, including its sequences.

    """
    db = req.app["db"]

    otu_id = req.match_info["otu_id"]
    isolate_id = req.match_info["isolate_id"]

    document = await db.otus.find_one({"_id": otu_id, "isolates.id": isolate_id}, ["isolates"])

    if not document:
        return not_found()

    isolate = dict(virtool.otus.utils.find_isolate(document["isolates"], isolate_id), sequences=[])

    cursor = db.sequences.find({"otu_id": otu_id, "isolate_id": isolate_id}, {"otu_id": False, "isolate_id": False})

    async for sequence in cursor:
        sequence["id"] = sequence.pop("_id")
        isolate["sequences"].append(sequence)

    return json_response(isolate)


@routes.post("/api/otus/{otu_id}/isolates", schema={
    "source_type": {
        "type": "string",
        "coerce": virtool.validators.strip,
        "default": ""
    },
    "source_name": {
        "type": "string",
        "coerce": virtool.validators.strip,
        "default": ""
    },
    "default": {
        "type": "boolean",
        "default": False
    }
})
async def add_isolate(req):
    """
    Add a new isolate to a otu.

    """
    db = req.app["db"]
    data = req["data"]

    otu_id = req.match_info["otu_id"]

    document = await db.otus.find_one(otu_id)

    if not document:
        return not_found()

    if not await virtool.references.db.check_right(req, document["reference"]["id"], "modify_otu"):
        return insufficient_rights()

    isolates = deepcopy(document["isolates"])

    # True if the new isolate should be default and any existing isolates should be non-default.
    will_be_default = not isolates or data["default"]

    # Get the complete, joined entry before the update.
    old = await virtool.otus.db.join(db, otu_id, document)

    # All source types are stored in lower case.
    data["source_type"] = data["source_type"].lower()

    if not await virtool.references.db.check_source_type(db, document["reference"]["id"], data["source_type"]):
        return bad_request("Source type is not allowed")

    # Set ``default`` to ``False`` for all existing isolates if the new one should be default.
    if isolates and data["default"]:
        for isolate in isolates:
            isolate["default"] = False

    # Force the new isolate as default if it is the first isolate.
    if not isolates:
        data["default"] = True

    # Set the isolate as the default isolate if it is the first one.
    data["default"] = will_be_default

    isolate_id = await virtool.otus.db.append_isolate(db, otu_id, isolates, data)

    # Get the joined entry now that it has been updated.
    new = await virtool.otus.db.join(db, otu_id)

    await virtool.otus.db.update_verification(db, new)

    isolate_name = virtool.otus.utils.format_isolate_name(data)

    description = f"Added {isolate_name}"

    if will_be_default:
        description += " as default"

    await virtool.history.db.add(
        db,
        "add_isolate",
        old,
        new,
        description,
        req["client"].user_id
    )

    headers = {
        "Location": f"/api/otus/{otu_id}/isolates/{isolate_id}"
    }

    return json_response(
        dict(data, id=isolate_id, sequences=[]),
        status=201,
        headers=headers
    )


@routes.patch("/api/otus/{otu_id}/isolates/{isolate_id}", schema={
    "source_type": {
        "type": "string",
        "coerce": virtool.validators.strip,
    },
    "source_name": {
        "type": "string",
        "coerce": virtool.validators.strip,
    }
})
async def edit_isolate(req):
    """
    Edit an existing isolate.

    """
    db = req.app["db"]
    data = req["data"]

    otu_id = req.match_info["otu_id"]
    isolate_id = req.match_info["isolate_id"]

    document = await db.otus.find_one({"_id": otu_id, "isolates.id": isolate_id})

    if not document:
        return not_found()

    ref_id = document["reference"]["id"]

    if not await virtool.references.db.check_right(req, ref_id, "modify_otu"):
        return insufficient_rights()

    reference = await db.references.find_one(ref_id, ["restrict_source_types", "source_types"])

    isolates = deepcopy(document["isolates"])

    isolate = virtool.otus.utils.find_isolate(isolates, isolate_id)

    # All source types are stored in lower case.
    if "source_type" in data:
        data["source_type"] = data["source_type"].lower()

        if reference["restrict_source_types"] and data["source_type"] not in reference["source_types"]:
            return bad_request("Source type is not allowed")

    old_isolate_name = virtool.otus.utils.format_isolate_name(isolate)

    isolate.update(data)

    old = await virtool.otus.db.join(db, otu_id)

    # Replace the isolates list with the update one.
    document = await db.otus.find_one_and_update({"_id": otu_id}, {
        "$set": {
            "isolates": isolates,
            "verified": False
        },
        "$inc": {
            "version": 1
        }
    })

    # Get the joined entry now that it has been updated.
    new = await virtool.otus.db.join(db, otu_id, document)

    await virtool.otus.db.update_verification(db, new)

    isolate_name = virtool.otus.utils.format_isolate_name(isolate)

    # Use the old and new entry to add a new history document for the change.
    await virtool.history.db.add(
        db,
        "edit_isolate",
        old,
        new,
        f"Renamed {old_isolate_name} to {isolate_name}",
        req["client"].user_id
    )

    complete = await virtool.otus.db.join_and_format(db, otu_id, joined=new)

    for isolate in complete["isolates"]:
        if isolate["id"] == isolate_id:
            return json_response(isolate, status=200)


@routes.put("/api/otus/{otu_id}/isolates/{isolate_id}/default")
async def set_as_default(req):
    """
    Set an isolate as default.

    """
    db = req.app["db"]

    otu_id = req.match_info["otu_id"]
    isolate_id = req.match_info["isolate_id"]

    document = await db.otus.find_one({"_id": otu_id, "isolates.id": isolate_id})

    if not document:
        return not_found()

    if not await virtool.references.db.check_right(req, document["reference"]["id"], "modify_otu"):
        return insufficient_rights()

    isolates = deepcopy(document["isolates"])

    isolate = virtool.otus.utils.find_isolate(isolates, isolate_id)

    # Set ``default`` to ``False`` for all existing isolates if the new one should be default.
    for existing_isolate in isolates:
        existing_isolate["default"] = False

    isolate["default"] = True

    if isolates == document["isolates"]:
        complete = await virtool.otus.db.join_and_format(db, otu_id)
        for isolate in complete["isolates"]:
            if isolate["id"] == isolate_id:
                return json_response(isolate)

    old = await virtool.otus.db.join(db, otu_id)

    # Replace the isolates list with the updated one.
    document = await db.otus.find_one_and_update({"_id": otu_id}, {
        "$set": {
            "isolates": isolates,
            "verified": False
        },
        "$inc": {
            "version": 1
        }
    })

    # Get the joined entry now that it has been updated.
    new = await virtool.otus.db.join(db, otu_id, document)

    await virtool.otus.db.update_verification(db, new)

    isolate_name = virtool.otus.utils.format_isolate_name(isolate)

    # Use the old and new entry to add a new history document for the change.
    await virtool.history.db.add(
        db,
        "set_as_default",
        old,
        new,
        f"Set {isolate_name} as default",
        req["client"].user_id
    )

    complete = await virtool.otus.db.join_and_format(db, otu_id, new)

    for isolate in complete["isolates"]:
        if isolate["id"] == isolate_id:
            return json_response(isolate)


@routes.delete("/api/otus/{otu_id}/isolates/{isolate_id}")
async def remove_isolate(req):
    """
    Remove an isolate and its sequences from a otu.

    """
    db = req.app["db"]

    otu_id = req.match_info["otu_id"]
    isolate_id = req.match_info["isolate_id"]

    document = await db.otus.find_one({"_id": otu_id, "isolates.id": isolate_id})

    if not document:
        return not_found()

    if not await virtool.references.db.check_right(req, document["reference"]["id"], "modify_otu"):
        return insufficient_rights()

    isolates = deepcopy(document["isolates"])

    # Get any isolates that have the isolate id to be removed (only one should match!).
    isolate_to_remove = virtool.otus.utils.find_isolate(isolates, isolate_id)

    # Remove the isolate from the otu' isolate list.
    isolates.remove(isolate_to_remove)

    new_default = None

    # Set the first isolate as default if the removed isolate was the default.
    if isolate_to_remove["default"] and len(isolates):
        new_default = isolates[0]
        new_default["default"] = True

    old = await virtool.otus.db.join(db, otu_id, document)

    document = await db.otus.find_one_and_update({"_id": otu_id}, {
        "$set": {
            "isolates": isolates,
            "verified": False
        },
        "$inc": {
            "version": 1
        }
    })

    new = await virtool.otus.db.join(db, otu_id, document)

    issues = await virtool.otus.db.verify(db, otu_id, joined=new)

    if issues is None:
        await db.otus.update_one({"_id": otu_id}, {
            "$set": {
                "verified": True
            }
        })

        new["verified"] = True

    # Remove any sequences associated with the removed isolate.
    await db.sequences.delete_many({"otu_id": otu_id, "isolate_id": isolate_id})

    old_isolate_name = virtool.otus.utils.format_isolate_name(isolate_to_remove)

    description = f"Removed {old_isolate_name}"

    if isolate_to_remove["default"] and new_default:
        new_isolate_name = virtool.otus.utils.format_isolate_name(new_default)
        description += f" and set {new_isolate_name} as default"

    await virtool.history.db.add(
        db,
        "remove_isolate",
        old,
        new,
        description,
        req["client"].user_id
    )

    return no_content()


@routes.get("/api/otus/{otu_id}/isolates/{isolate_id}/sequences")
async def list_sequences(req):
    db = req.app["db"]

    otu_id = req.match_info["otu_id"]
    isolate_id = req.match_info["isolate_id"]

    if not await db.otus.find({"_id": otu_id, "isolates.id": isolate_id}).count():
        return not_found()

    projection = list(virtool.otus.db.SEQUENCE_PROJECTION)

    projection.remove("otu_id")
    projection.remove("isolate_id")

    cursor = db.sequences.find({"otu_id": otu_id, "isolate_id": isolate_id}, projection)

    return json_response([virtool.utils.base_processor(d) async for d in cursor])


@routes.get("/api/otus/{otu_id}/isolates/{isolate_id}/sequences/{sequence_id}")
async def get_sequence(req):
    """
    Get a single sequence document by its ``accession`.

    """
    db = req.app["db"]

    otu_id = req.match_info["otu_id"]
    isolate_id = req.match_info["isolate_id"]
    sequence_id = req.match_info["sequence_id"]

    if not await db.otus.count({"_id": otu_id, "isolates.id": isolate_id}):
        return not_found()

    query = {
        "_id": sequence_id,
        "otu_id": otu_id,
        "isolate_id": isolate_id
    }

    document = await db.sequences.find_one(query, virtool.otus.db.SEQUENCE_PROJECTION)

    if not document:
        return not_found()

    return json_response(virtool.utils.base_processor(document))


@routes.post("/api/otus/{otu_id}/isolates/{isolate_id}/sequences", schema={
    "accession": {
        "type": "string",
        "coerce": virtool.validators.strip,
        "empty": False,
        "required": True
    },
    "definition": {
        "type": "string",
        "coerce": virtool.validators.strip,
        "empty": False,
        "required": True
    },
    "host": {
        "type": "string",
        "coerce": virtool.validators.strip,
    },
    "segment": {
        "type": "string",
    },
    "sequence": {
        "type": "string",
        "coerce": virtool.validators.strip,
        "empty": False,
        "required": True
    }
})
async def create_sequence(req):
    """
    Create a new sequence record for the given isolate.

    """
    db, data = req.app["db"], req["data"]

    # Extract variables from URL path.
    otu_id, isolate_id = (req.match_info[key] for key in ["otu_id", "isolate_id"])

    # Get the subject otu document. Will be ``None`` if it doesn't exist. This will result in a ``404`` response.
    document = await db.otus.find_one({"_id": otu_id, "isolates.id": isolate_id})

    if not document:
        return not_found()

    ref_id = document["reference"]["id"]

    if not await virtool.references.db.check_right(req, ref_id, "modify_otu"):
        return insufficient_rights()

    segment = data.get("segment", None)

    if segment and segment not in {s["name"] for s in document.get("schema", {})}:
        return bad_request("Segment does not exist")

    # Update POST data to make sequence document.
    data.update({
        "otu_id": otu_id,
        "isolate_id": isolate_id,
        "host": data.get("host", ""),
        "reference": {
            "id": ref_id
        },
        "segment": segment,
        "sequence": data["sequence"].replace(" ", "").replace("\n", "")
    })

    old = await virtool.otus.db.join(db, otu_id, document)

    sequence_document = await db.sequences.insert_one(data)

    new = await db.otus.find_one_and_update({"_id": otu_id}, {
        "$set": {
            "verified": False
        },
        "$inc": {
            "version": 1
        }
    })

    new = await virtool.otus.db.join(db, otu_id, new)

    await virtool.otus.db.update_verification(db, new)

    isolate = virtool.otus.utils.find_isolate(old["isolates"], isolate_id)

    await virtool.history.db.add(
        db,
        "create_sequence",
        old,
        new,
        f"Created new sequence {data['accession']} in {virtool.otus.utils.format_isolate_name(isolate)}",
        req["client"].user_id
    )

    headers = {
        "Location": f"/api/otus/{otu_id}/isolates/{isolate_id}/sequences/{sequence_document['_id']}"
    }

    return json_response(virtool.utils.base_processor(data), status=201, headers=headers)


@routes.patch("/api/otus/{otu_id}/isolates/{isolate_id}/sequences/{sequence_id}", schema={
    "accession": {
        "type": "string",
        "coerce": virtool.validators.strip,
        "empty": False
    },
    "host": {
        "type": "string",
        "coerce": virtool.validators.strip
    },
    "definition": {
        "type": "string",
        "coerce": virtool.validators.strip,
        "empty": False
    },
    "segment": {
        "type": "string"
    },
    "sequence": {
        "type": "string",
        "coerce": virtool.validators.strip,
        "empty": False
    }
})
async def edit_sequence(req):
    db, data = req.app["db"], req["data"]

    otu_id, isolate_id, sequence_id = (req.match_info[key] for key in ["otu_id", "isolate_id", "sequence_id"])

    document = await db.otus.find_one({"_id": otu_id, "isolates.id": isolate_id})

    if not document or not await db.sequences.count({"_id": sequence_id}):
        return not_found()

    if not await virtool.references.db.check_right(req, document["reference"]["id"], "modify_otu"):
        return insufficient_rights()

    old = await virtool.otus.db.join(db, otu_id, document)

    segment = data.get("segment", None)

    if segment and segment not in {s["name"] for s in document.get("schema", {})}:
        return not_found("Segment does not exist")

    data["sequence"] = data["sequence"].replace(" ", "").replace("\n", "")

    updated_sequence = await db.sequences.find_one_and_update({"_id": sequence_id}, {
        "$set": data
    })

    document = await db.otus.find_one_and_update({"_id": otu_id}, {
        "$set": {
            "verified": False
        },
        "$inc": {
            "version": 1
        }
    })

    new = await virtool.otus.db.join(db, otu_id, document)

    await virtool.otus.db.update_verification(db, new)

    isolate = virtool.otus.utils.find_isolate(old["isolates"], isolate_id)

    await virtool.history.db.add(
        db,
        "edit_sequence",
        old,
        new,
        f"Edited sequence {sequence_id} in {virtool.otus.utils.format_isolate_name(isolate)}",
        req["client"].user_id
    )

    return json_response(virtool.utils.base_processor(updated_sequence))


@routes.delete("/api/otus/{otu_id}/isolates/{isolate_id}/sequences/{sequence_id}")
async def remove_sequence(req):
    """
    Remove a sequence from an isolate.

    """
    db = req.app["db"]

    otu_id = req.match_info["otu_id"]
    isolate_id = req.match_info["isolate_id"]
    sequence_id = req.match_info["sequence_id"]

    if not await db.sequences.count({"_id": sequence_id}):
        return not_found()

    old = await virtool.otus.db.join(db, {"_id": otu_id, "isolates.id": isolate_id})

    if old is None:
        return not_found()

    if not await virtool.references.db.check_right(req, old["reference"]["id"], "modify_otu"):
        return insufficient_rights()

    isolate = virtool.otus.utils.find_isolate(old["isolates"], isolate_id)

    await db.sequences.delete_one({"_id": sequence_id})

    await db.otus.update_one({"_id": otu_id}, {
        "$set": {
            "verified": False
        },
        "$inc": {
            "version": 1
        }
    })

    new = await virtool.otus.db.join(db, otu_id)

    await virtool.otus.db.update_verification(db, new)

    isolate_name = virtool.otus.utils.format_isolate_name(isolate)

    await virtool.history.db.add(
        db,
        "remove_sequence",
        old,
        new,
        f"Removed sequence {sequence_id} from {isolate_name}",
        req["client"].user_id
    )

    return no_content()


@routes.get("/api/otus/{otu_id}/history")
async def list_history(req):
    db = req.app["db"]

    otu_id = req.match_info["otu_id"]

    if not await db.otus.find({"_id": otu_id}).count():
        return not_found()

    cursor = db.history.find({"otu.id": otu_id})

    return json_response([d async for d in cursor])
