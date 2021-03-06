import React from "react";
import CX from "classnames";
import { connect } from "react-redux";
import { LinkContainer } from "react-router-bootstrap";
import { Row, Col } from "react-bootstrap";

import { getTaskDisplayName } from "../../utils/utils";
import { Icon, Label, Loader, RelativeTime } from "../../base";
import { removeAnalysis } from "../actions";
import { getCanModify } from "../../samples/selectors";

export const RightIcon = ({ canModify, onRemove, ready }) => {
    if (ready) {
        if (canModify) {
            return <Icon name="trash" bsStyle="danger" onClick={onRemove} style={{ fontSize: "17px" }} pullRight />;
        }

        return null;
    }

    return (
        <div className="pull-right">
            <Loader size="14px" color="#3c8786" />
        </div>
    );
};

export const AnalysisItem = props => {
    const itemClass = CX("list-group-item spaced", { hoverable: props.ready });

    const reference = props.placeholder ? null : (
        <span>
            <span>{props.reference.name} </span>
            <Label>{props.index.version}</Label>
        </span>
    );

    const content = (
        <div className={itemClass} style={{ color: "#555" }}>
            <Row>
                <Col xs={4} sm={4} md={4}>
                    <strong>{getTaskDisplayName(props.algorithm)}</strong>
                </Col>
                <Col xs={5} sm={4} md={4}>
                    Started <RelativeTime time={props.created_at} />
                    {props.placeholder ? null : ` by ${props.user.id}`}
                </Col>
                <Col xs={2}>{reference}</Col>
                <Col xsHidden sm={2} md={2}>
                    <RightIcon canModify={props.canModify} ready={props.ready} onRemove={props.onRemove} />
                </Col>
            </Row>
        </div>
    );

    if (props.placeholder) {
        return content;
    }

    return <LinkContainer to={`/samples/${props.sampleId}/analyses/${props.id}`}>{content}</LinkContainer>;
};

export const mapStateToProps = state => ({
    sampleId: state.samples.detail.id,
    canModify: getCanModify(state)
});

export const mapDispatchToProps = (dispatch, ownProps) => ({
    onRemove: () => {
        dispatch(removeAnalysis(ownProps.id));
    }
});

export default connect(
    mapStateToProps,
    mapDispatchToProps
)(AnalysisItem);
