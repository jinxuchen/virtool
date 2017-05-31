/**
 *
 *
 * @copyright 2017 Government of Canada
 * @license MIT
 * @author igboyes
 *
 */

import React from "react";
import { connect } from "react-redux";
import { withRouter, Redirect, Route } from "react-router-dom";
import { Nav, NavItem } from "react-bootstrap";
import { LinkContainer } from "react-router-bootstrap";

import { Flex, FlexItem } from "virtool/js/components/Base";
import { getSettings } from "../actions";
import GeneralSettings from "./General";

const Settings = (props) => {
    return (
        <div className="container">
            <Redirect from="/settings" to="/settings/general" />

            <Flex>
                <FlexItem>
                    <Nav bsStyle="pills" stacked>
                        <LinkContainer to="/settings/general">
                            <NavItem>General</NavItem>
                        </LinkContainer>

                        <LinkContainer to="/settings/server">
                            <NavItem>Server</NavItem>
                        </LinkContainer>

                        <LinkContainer to="/settings/Database">
                            <NavItem>Database</NavItem>
                        </LinkContainer>
                    </Nav>
                </FlexItem>

                <FlexItem pad={15}>
                    <div style={{borderRight: "1px solid #e5e5e5", height: "100%"}} />
                </FlexItem>

                <FlexItem pad={15}>
                    <Route path="/settings/general" render={() => (<GeneralSettings {...props} />)} />
                </FlexItem>
            </Flex>
        </div>
    );
};

Settings.propTypes = {
    source_types: React.PropTypes.object,
    get: React.PropTypes.func
};

const mapStateToProps = (state) => {
    return {
        restrictSourceTypes: state.settings.restrict_source_types,
        allowedSourceTypes: state.settings.allowed_source_types
    };
};

const mapDispatchToProps = (dispatch) => {
    return {

        get: () => {
            dispatch(getSettings())
        },

        set: (key, value) => {
            console.log(key, value);
        }

    };
};

const SettingsContainer = withRouter(connect(
    mapStateToProps,
    mapDispatchToProps
)(Settings));

export default SettingsContainer;
