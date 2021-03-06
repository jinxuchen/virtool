import React from "react";
import styled from "styled-components";
import { connect } from "react-redux";
import { push } from "connected-react-router";
import { Modal } from "react-bootstrap";
import { routerLocationHasState } from "../../utils/utils";
import { TabLink, Tabs } from "../../base";

import ImportReference from "./Import";
import CreateReference from "./Create";
import CloneReference from "./Clone";

const AddReferenceTabs = styled(Tabs)`
    margin-bottom: 0;
`;

export class AddReference extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            lock: false
        };
    }

    componentDidUpdate(prevProps) {
        if (this.props.show !== prevProps.show) {
            this.setState({ show: this.props.show });
        }
    }

    checkActive = current => () => this.props[current];

    checkModalLock = isLocked => {
        if (isLocked) {
            return this.setState({ lock: true });
        }
        this.setState({ lock: false });
    };

    handleHide = () => {
        if (!this.state.lock) {
            this.props.onHide();
        }
    };

    renderForm = () => {
        if (this.props.isImport) {
            return <ImportReference lock={this.checkModalLock} />;
        }

        if (this.props.isClone) {
            return <CloneReference />;
        }

        return <CreateReference />;
    };

    render() {
        return (
            <Modal show={this.props.show} onHide={this.handleHide} onExited={this.props.onHide}>
                <Modal.Header onHide={this.handleHide} style={{ borderBottomWidth: "0" }} closeButton>
                    New Reference
                </Modal.Header>

                <AddReferenceTabs>
                    <TabLink
                        to={{ state: { newReference: true, createReference: true } }}
                        isActive={this.checkActive("isCreate")}
                    >
                        Create
                    </TabLink>
                    <TabLink
                        to={{ state: { newReference: true, importReference: true } }}
                        isActive={this.checkActive("isImport")}
                    >
                        Import
                    </TabLink>
                    <TabLink
                        to={{ state: { newReference: true, cloneReference: true } }}
                        isActive={this.checkActive("isClone")}
                    >
                        Clone
                    </TabLink>
                </AddReferenceTabs>

                {this.renderForm()}
            </Modal>
        );
    }
}

const mapStateToProps = state => {
    const isClone = routerLocationHasState(state, "cloneReference");
    const isCreate = routerLocationHasState(state, "createReference");
    const isImport = routerLocationHasState(state, "importReference");

    return {
        show: routerLocationHasState(state, "newReference"),
        isCreate,
        isImport,
        isClone
    };
};

const mapDispatchToProps = dispatch => ({
    onHide: () => {
        dispatch(push({ state: { newReference: false } }));
    }
});

export default connect(
    mapStateToProps,
    mapDispatchToProps
)(AddReference);
