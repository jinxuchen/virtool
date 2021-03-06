/**
 * @license
 * The MIT License (MIT)
 * Copyright 2015 Government of Canada
 *
 * @author
 * Ian Boyes
 *
 * @exports GroupsPermissions
 */

import { transform } from "lodash-es";
import PropTypes from "prop-types";
import React from "react";
import { Col, Row } from "react-bootstrap";
import { Icon, ListGroupItem, Panel } from "../../base";

const UserPermissions = ({ permissions }) => {
    const permissionComponents = transform(
        permissions,
        (acc, value, permission) => {
            acc.push(
                <Col key={permission} xs={12} md={3}>
                    <ListGroupItem bsStyle={value ? "success" : "danger"} style={{ marginRight: "3px" }}>
                        <code>{permission}</code> <Icon name={value ? "check" : "times"} pullRight />
                    </ListGroupItem>
                </Col>
            );

            return acc;
        },
        []
    );

    return (
        <Panel>
            <Panel.Body>
                <Row>{permissionComponents}</Row>
            </Panel.Body>
        </Panel>
    );
};

UserPermissions.propTypes = {
    permissions: PropTypes.object
};

export default UserPermissions;
