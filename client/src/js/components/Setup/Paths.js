/**
 * @license
 * The MIT License (MIT)
 * Copyright 2015 Government of Canada
 *
 * @author
 * Ian Boyes
 *
 * @exports SetupDatabase
 */

import React from "react";
import { Alert } from "react-bootstrap";
import { Icon, Input, Button } from "virtool/js/components/Base";
import { postJSON } from "virtool/js/utils";

export default class SetupDatabase extends React.Component {

    constructor (props) {
        super(props);
        this.state = {
            dataPath: this.props.dataPath,
            watchPath: this.props.watchPath
        };
    }

    static propTypes = {
        host: React.PropTypes.string,
        port: React.PropTypes.number,
        dataPath: React.PropTypes.string,
        watchPath: React.PropTypes.string,
        checkedName: React.PropTypes.func,
        hasCollections: React.PropTypes.bool
    };

    componentDidMount () {
        this.refs.first.focus();
    }

    handleChange = (event) => {
        let data = {};
        data[event.target.name] = event.target.value;
        this.setState(data);
    };

    handleSubmit = (event) => {
        event.preventDefault();

        const args = {
            host: this.props.host,
            port: this.props.port,
            name: this.state.name,
            operation: "check_db"
        };

        postJSON("/", args, (data) => {
            this.setState({pending: false}, () => {
                if (!data.error) {
                    data.name = this.state.name;
                    this.props.checkedName(data);
                }
            });
        });
    };

    render () {

        let alert;

        if (this.props.hasCollections) {
            alert = (
                <Alert bsStyle="danger">
                    <span>
                        The chosen database already exists and contains Virtool data collections. These collections
                        require matching files on disk to work properly. Virtool will not work if the paths entered
                        below do not match the paths used when database records were created.
                    </span>
                </Alert>
            );
        }

        return (
            <form onSubmit={this.handleSubmit}>
                {alert}

                <Input
                    type="text"
                    inputRef={input => input.focus()}
                    name="dataPath"
                    label="Data Path"
                    onChange={this.handleChange}
                    value={this.state.dataPath}
                />

                <Input
                    type="text"
                    name="watchPath"
                    label="Watch Path"
                    onChange={this.handleChange}
                    value={this.state.watchPath}
                />

                <Button bsStyle="primary" className="pull-right" type="submit">
                    <Icon name="floppy" /> Save
                </Button>
            </form>
        );
    }
}
