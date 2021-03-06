/**
 *
 *
 * @copyright 2017 Government of Canada
 * @license MIT
 * @author igboyes
 *
 */
import React from "react";
import PropTypes from "prop-types";
import { get, groupBy, map, reverse, sortBy } from "lodash-es";
import { connect } from "react-redux";
import { Row, Col, ListGroup } from "react-bootstrap";
import { checkRefRight } from "../../../utils/utils";

import { getOTUHistory, revert } from "../../actions";
import { Flex, FlexItem, ListGroupItem, RelativeTime, Icon, Label, LoadingPlaceholder } from "../../../base";

const methodIconProps = {
    add_isolate: {
        name: "flask",
        bsStyle: "primary"
    },
    create: {
        name: "plus-square",
        bsStyle: "primary"
    },
    create_sequence: {
        name: "dna",
        bsStyle: "primary"
    },
    edit: {
        name: "pencil-alt",
        bsStyle: "warning"
    },
    edit_isolate: {
        name: "flask",
        bsStyle: "warning"
    },
    edit_sequence: {
        name: "dna",
        bsStyle: "warning"
    },
    clone: {
        name: "clone",
        bsStyle: "primary"
    },
    import: {
        name: "file-import",
        bsStyle: "primary"
    },
    remote: {
        name: "link",
        bsStyle: "primary"
    },
    remove: {
        name: "trash",
        bsStyle: "danger"
    },
    remove_isolate: {
        name: "flask",
        bsStyle: "danger"
    },
    remove_sequence: {
        name: "dna",
        bsStyle: "danger"
    },
    set_as_default: {
        name: "star",
        bsStyle: "warning"
    },
    update: {
        name: "arrow-alt-circle-up",
        bsStyle: "warning"
    }
};

const getMethodIcon = ({ method_name }) => {
    const props = get(methodIconProps, method_name, {
        name: "exclamation-triangle",
        bsStyle: "danger"
    });

    return <Icon {...props} />;
};

export class Change extends React.Component {
    handleRevert = () => {
        this.props.revert(this.props.otu.id, this.props.otu.version, this.props._id);
    };

    render() {
        let revertIcon;

        if (this.props.unbuilt && this.props.canModify) {
            revertIcon = <Icon name="undo" bsStyle="primary" tip="Revert" onClick={this.handleRevert} pullRight />;
        }

        return (
            <ListGroupItem>
                <Row>
                    <Col md={1}>
                        <Label>{this.props.otu.version}</Label>
                    </Col>
                    <Col md={6}>
                        <Flex alignItems="center">
                            {getMethodIcon(this.props)}
                            <FlexItem pad={5}>{this.props.description || "No Description"}</FlexItem>
                        </Flex>
                    </Col>
                    <Col md={4}>
                        <RelativeTime time={this.props.created_at} /> by {this.props.user.id}
                    </Col>
                    <Col md={1}>{revertIcon}</Col>
                </Row>
            </ListGroupItem>
        );
    }
}

export class HistoryList extends React.Component {
    render() {
        const changes = reverse(sortBy(this.props.history, "otu.version"));

        const changeComponents = map(changes, (change, index) => (
            <Change
                key={index}
                {...change}
                canModify={this.props.canModify}
                unbuilt={this.props.unbuilt}
                revert={this.props.revert}
            />
        ));

        return <ListGroup>{changeComponents}</ListGroup>;
    }
}

HistoryList.propTypes = {
    history: PropTypes.arrayOf(PropTypes.object),
    unbuilt: PropTypes.bool,
    revert: PropTypes.func,
    canModify: PropTypes.bool
};

class OTUHistory extends React.Component {
    componentDidMount() {
        this.props.getHistory(this.props.otuId);
    }

    render() {
        if (this.props.history === null) {
            return <LoadingPlaceholder />;
        }

        const changes = groupBy(this.props.history, change =>
            change.index.version === "unbuilt" ? "unbuilt" : "built"
        );

        let built;
        let unbuilt;

        if (changes.built) {
            built = (
                <div>
                    <h4>Built Changes</h4>
                    <HistoryList history={changes.built} canModify={this.props.canModify} />
                </div>
            );
        }

        if (changes.unbuilt) {
            unbuilt = (
                <div>
                    <h4>Unbuilt Changes</h4>
                    <HistoryList
                        history={changes.unbuilt}
                        revert={this.props.revert}
                        canModify={this.props.canModify}
                        unbuilt
                    />
                </div>
            );
        }

        return (
            <div>
                {unbuilt}
                {built}
            </div>
        );
    }
}

const mapStateToProps = state => ({
    otuId: state.otus.detail.id,
    history: state.otus.detailHistory,
    canModify: !get(state, "references.detail.remotes_from") && checkRefRight(state, "modify_otu")
});

const mapDispatchToProps = dispatch => ({
    getHistory: otuId => {
        dispatch(getOTUHistory(otuId));
    },

    revert: (otuId, otuVersion, changeId) => {
        dispatch(revert(otuId, otuVersion, changeId));
    }
});

export default connect(
    mapStateToProps,
    mapDispatchToProps
)(OTUHistory);
