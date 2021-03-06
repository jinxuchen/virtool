import { map, sortBy } from "lodash-es";
import React from "react";
import { ListGroup } from "react-bootstrap";
import { connect } from "react-redux";
import { Link } from "react-router-dom";
import { Badge, ListGroupItem, NoneFound, Panel, RelativeTime, Table } from "../../../base";
import { checkUpdates, updateRemoteReference } from "../../actions";
import RemoteReference from "./Remote";

const Clone = ({ source }) => (
    <Panel>
        <Panel.Heading>Clone Reference</Panel.Heading>
        <ListGroup>
            <ListGroupItem>
                <strong>Source Reference</strong>
                <span>
                    {" / "}
                    <a href={`/refs/${source.id}`}>{source.name}</a>
                </span>
            </ListGroupItem>
        </ListGroup>
    </Panel>
);

const Contributors = ({ contributors }) => {
    if (contributors.length) {
        const sorted = sortBy(contributors, ["id", "count"]);

        const contributorComponents = map(sorted, entry => (
            <ListGroupItem key={entry.id}>
                {entry.id} <Badge>{entry.count}</Badge>
            </ListGroupItem>
        ));

        return <ListGroup>{contributorComponents}</ListGroup>;
    }

    return <NoneFound noun="contributors" />;
};

const LatestBuild = ({ id, latestBuild }) => {
    if (latestBuild) {
        return (
            <ListGroupItem>
                <strong>
                    <Link to={`/refs/${id}/indexes/${latestBuild.id}`}>Index {latestBuild.version}</Link>
                </strong>
                <span>
                    &nbsp;/ Created <RelativeTime time={latestBuild.created_at} /> by {latestBuild.user.id}
                </span>
            </ListGroupItem>
        );
    }

    return <NoneFound noun="builds" noListGroup />;
};

const ReferenceManage = ({ detail }) => {
    const { id, cloned_from, contributors, description, latest_build, organism, remotes_from } = detail;

    let remote;
    let clone;

    if (remotes_from) {
        remote = <RemoteReference />;
    }

    if (cloned_from) {
        clone = <Clone source={cloned_from} />;
    }

    return (
        <div>
            <Table>
                <tbody>
                    <tr>
                        <th>Description</th>
                        <td>{description}</td>
                    </tr>
                    <tr>
                        <th>Organism</th>
                        <td className="text-capitalize">{organism}</td>
                    </tr>
                </tbody>
            </Table>

            {remote}
            {clone}

            <Panel>
                <Panel.Heading>Latest Index Build</Panel.Heading>

                <ListGroup>
                    <LatestBuild refId={id} latestBuild={latest_build} />
                </ListGroup>
            </Panel>

            <Panel>
                <Panel.Heading>Contributors</Panel.Heading>
                <Contributors contributors={contributors} />
            </Panel>
        </div>
    );
};

const mapStateToProps = state => ({
    detail: state.references.detail
});

const mapDispatchToProps = dispatch => ({
    onCheckUpdates: refId => {
        dispatch(checkUpdates(refId));
    },

    onUpdate: refId => {
        dispatch(updateRemoteReference(refId));
    }
});

export default connect(
    mapStateToProps,
    mapDispatchToProps
)(ReferenceManage);
