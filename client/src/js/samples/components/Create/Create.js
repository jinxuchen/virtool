import React from "react";
import { filter, map, replace, split, upperFirst, get } from "lodash-es";
import { connect } from "react-redux";
import {
    Modal,
    Row,
    Col,
    ControlLabel,
    InputGroup
} from "react-bootstrap";
import { push } from "react-router-redux";

import ReadSelector from "./ReadSelector";
import { findReadyHosts, createSample } from "../../actions";
import { clearError } from "../../../errors/actions";
import { Button, Icon, InputError, LoadingPlaceholder } from "../../../base";
import { findFiles } from "../../../files/actions";
import { routerLocationHasState } from "../../../utils";

const getReadyHosts = (props) => (
    props.readyHosts && props.readyHosts.length ? (props.readyHosts[0].id || "") : ""
);

const getInitialState = (props) => ({
    selected: [],
    name: "",
    host: "",
    isolate: "",
    locale: "",
    subtraction: getReadyHosts(props),
    group: props.forceGroupChoice ? "none" : "",
    errorName: "",
    errorSubtraction: "",
    errorFile: ""
});

const SampleUserGroup = ({ group, groups, onChange }) => {
    const groupComponents = map(groups, groupId =>
        <option key={groupId} value={groupId} className="text-capitalize">
            {groupId}
        </option>
    );

    return (
        <Col md={3}>
            <InputError type="select" label="User Group" value={group} onChange={onChange}>
                <option key="none" value="none">None</option>
                {groupComponents}
            </InputError>
        </Col>
    );
};

class CreateSample extends React.Component {

    constructor (props) {
        super(props);
        this.state = getInitialState(props);
    }

    componentWillReceiveProps (nextProps) {
        if (nextProps.readyHosts !== this.props.readyHosts) {
            return this.setState({subtraction: getReadyHosts(nextProps)});
        }

        if (!this.props.error && nextProps.error) {
            this.setState({
                errorName: nextProps.error
            });
        }
    }

    modalEnter = () => {
        this.props.onFindHosts();
        this.props.onFindFiles();
    };

    handleHide = () => {
        this.props.onHide();
        if (this.state.error) {
            this.props.onClearError("UPDATE_SAMPLE_ERROR");
        }
    };

    handleModalExited = () => {
        this.setState(getInitialState(this.props));
    };

    handleChange = (e) => {
        const name = e.target.name;

        if (name === "name" || name === "subtraction") {
            const errorType = `error${upperFirst(name)}`;

            this.setState({
                [name]: e.target.value,
                [errorType]: ""
            });

            if (this.state.errorName) {
                this.props.onClearError("CREATE_SAMPLE_ERROR");
            }
        } else {
            this.setState({
                [name]: e.target.value
            });
        }

    };

    handleSubmit = (e) => {
        e.preventDefault();

        let error = "";

        if (!this.state.name) {
            error = "Required Field";
            this.setState({ errorName: error });
        }

        if (!this.props.readyHosts || !this.props.readyHosts.length) {
            error = "A host genome must be added to Virtool before samples can be created and analyzed.";
            this.setState({ errorSubtraction: error });
        }

        if (!this.state.selected.length) {
            error = "At least one read file must be attached to the sample";
            this.setState({ errorFile: error });
        }

        if (!error) {
            this.props.onCreate({...this.state, files: this.state.selected});
        }
    };

    autofill = () => {
        this.setState({
            name: split(replace(this.state.selected[0], /[0-9a-z]{8}-/, ""), /_S\d+/)[0]
        });
    };

    handleSelect = (selected) => {
        this.setState({ selected, errorFile: "" });
    };

    render () {

        if (this.props.readyHosts === null || this.props.readFiles) {
            return (
                <Modal show={this.props.show} onHide={this.props.onHide} onEnter={this.modalEnter}>
                    <Modal.Body>
                        <LoadingPlaceholder margin="36px" />
                    </Modal.Body>
                </Modal>
            );
        }

        const hostComponents = map(this.props.readyHosts, host =>
            <option key={host.id}>{host.id}</option>
        );

        const userGroup = this.props.forceGroupChoice ? (
            <SampleUserGroup
                group={this.props.group}
                groups={this.props.groups}
                onChange={(e) => this.setState({group: e})}
            />
        ) : null;

        const libraryType = this.state.selected.length === 2 ? "Paired" : "Unpaired";

        const { errorName, errorSubtraction, errorFile } = this.state;

        return (
            <Modal
                bsSize="large"
                show={this.props.show}
                onHide={this.handleHide}
                onEnter={this.modalEnter}
                onExited={this.handleModalExited}
            >
                <Modal.Header onHide={this.handleHide} closeButton>
                    Create Sample
                </Modal.Header>

                <form onSubmit={this.handleSubmit}>
                    <Modal.Body>

                        <Row>
                            <Col md={6}>
                                <ControlLabel>Sample Name</ControlLabel>
                                <InputGroup>
                                    <InputError
                                        name="name"
                                        value={this.state.name}
                                        onChange={this.handleChange}
                                        autocomplete={false}
                                        error={errorName}
                                    />
                                    <InputGroup.Button style={{verticalAlign: "top", zIndex: "0"}}>
                                        <Button
                                            type="button"
                                            onClick={this.autofill}
                                            disabled={!this.state.selected.length}
                                        >
                                            <Icon name="wand" />
                                        </Button>
                                    </InputGroup.Button>
                                </InputGroup>
                            </Col>
                            <Col md={6}>
                                <InputError
                                    name="isolate"
                                    label="Isolate"
                                    value={this.state.isolate}
                                    onChange={this.handleChange}
                                />
                            </Col>
                        </Row>

                        <Row>
                            <Col md={6}>
                                <InputError
                                    name="host"
                                    label="True Host"
                                    value={this.state.host}
                                    onChange={this.handleChange}
                                />
                            </Col>
                            <Col md={6}>
                                <InputError
                                    name="subtraction"
                                    type="select"
                                    label="Subtraction Host"
                                    value={this.state.subtraction}
                                    onChange={this.handleChange}
                                    error={errorSubtraction}
                                >
                                    {hostComponents}
                                </InputError>
                            </Col>
                        </Row>

                        <Row>
                            <Col md={6}>
                                <InputError
                                    name="locale"
                                    label="Locale"
                                    value={this.state.locale}
                                    onChange={this.handleChange}
                                />
                            </Col>
                            {userGroup}
                            <Col md={6}>
                                <InputError
                                    type="text"
                                    label="Library Type"
                                    value={libraryType}
                                    readOnly={true}
                                />
                            </Col>
                        </Row>

                        <ReadSelector
                            files={this.props.readyReads}
                            selected={this.state.selected}
                            onSelect={this.handleSelect}
                            error={errorFile}
                        />

                    </Modal.Body>

                    <Modal.Footer>
                        <Button type="submit" bsStyle="primary">
                            <Icon name="floppy" /> Save
                        </Button>
                    </Modal.Footer>
                </form>
            </Modal>
        );
    }
}

const mapStateToProps = (state) => {
    const show = routerLocationHasState(state, "create", true);

    return {
        show,
        groups: state.account.groups,
        readyHosts: state.samples.readyHosts,
        readyReads: filter(state.files.documents, {type: "reads", reserved: false}),
        forceGroupChoice: state.settings.sample_group === "force_choice",
        error: get(state, "errors.CREATE_SAMPLE_ERROR.message", "")
    };
};

const mapDispatchToProps = (dispatch) => ({

    onFindHosts: () => {
        dispatch(findReadyHosts());
    },

    onFindFiles: () => {
        dispatch(findFiles("reads", 1));
    },

    onCreate: ({ name, isolate, host, locale, subtraction, files }) => {
        dispatch(createSample(name, isolate, host, locale, subtraction, files));
    },

    onHide: () => {
        dispatch(push({...window.location, state: {create: false}}));
    },

    onClearError: (error) => {
        dispatch(clearError(error));
    }

});

export default connect(mapStateToProps, mapDispatchToProps)(CreateSample);
