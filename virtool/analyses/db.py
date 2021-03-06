import os

import virtool.analyses.utils
import virtool.bio
import virtool.db.utils
import virtool.history.db
import virtool.indexes.db
import virtool.jobs.db
import virtool.otus.utils
import virtool.samples.db
import virtool.utils

PROJECTION = [
    "_id",
    "algorithm",
    "created_at",
    "ready",
    "job",
    "index",
    "reference",
    "user",
    "sample"
]


async def new(app, sample_id, ref_id, user_id, algorithm):
    """
    Creates a new analysis. Ensures that a valid subtraction host was the submitted. Configures read and write
    permissions on the sample document and assigns it a creator username based on the requesting connection.

    """
    db = app["db"]
    settings = app["settings"]

    # Get the current id and version of the otu index currently being used for analysis.
    index_id, index_version = await virtool.indexes.db.get_current_id_and_version(db, ref_id)

    sample = await db.samples.find_one(sample_id, ["name"])

    analysis_id = await virtool.db.utils.get_new_id(db.analyses)

    job_id = await virtool.db.utils.get_new_id(db.jobs)

    document = {
        "_id": analysis_id,
        "ready": False,
        "created_at": virtool.utils.timestamp(),
        "job": {
            "id": job_id
        },
        "algorithm": algorithm,
        "sample": {
            "id": sample_id
        },
        "index": {
            "id": index_id,
            "version": index_version
        },
        "reference": {
            "id": ref_id,
            "name": await virtool.db.utils.get_one_field(db.references, "name", ref_id)
        },
        "user": {
            "id": user_id,
        }
    }

    task_args = {
        "analysis_id": analysis_id,
        "ref_id": ref_id,
        "sample_id": sample_id,
        "sample_name": sample["name"],
        "index_id": index_id
    }

    await db.analyses.insert_one(document)

    # Create job document.
    job = await virtool.jobs.db.create(
        db,
        settings,
        document["algorithm"],
        task_args,
        user_id
    )

    await app["jobs"].enqueue(job["_id"])

    await virtool.samples.db.recalculate_algorithm_tags(db, sample_id)

    return document


async def update_nuvs_blast(db, settings, analysis_id, sequence_index, rid):
    """
    Update the BLAST data for a sequence in a NuVs analysis.

    :param settings:
    :param db:

    :param analysis_id:
    :param sequence_index:
    :param rid:

    :return: the blast data and the complete analysis document
    :rtype: Tuple[dict, dict]

    """
    # Do initial check of RID to populate BLAST embedded document.
    data = {
        "rid": rid,
        "ready": await virtool.bio.check_rid(settings, rid),
        "last_checked_at": virtool.utils.timestamp(),
        "interval": 3
    }

    document = await db.analyses.find_one_and_update({"_id": analysis_id, "results.index": sequence_index}, {
        "$set": {
            "results.$.blast": data
        }
    })

    return data, document


async def remove_orphaned_directories(app):
    """
    Remove all analysis directories for which an analysis document does not exist in the database.

    :param app:
    """
    db = app["db"]

    samples_path = os.path.join(app["settings"]["data_path"], "samples")

    existing_ids = set(await db.analyses.distinct("_id"))

    for sample_id in os.listdir(samples_path):
        analyses_path = os.path.join(samples_path, sample_id, "analysis")

        to_delete = set(os.listdir(analyses_path)) - existing_ids

        for analysis_id in to_delete:
            analysis_path = os.path.join(analyses_path, analysis_id)
            try:
                await app["run_in_thread"](virtool.utils.rm, analysis_path, True)
            except FileNotFoundError:
                pass
