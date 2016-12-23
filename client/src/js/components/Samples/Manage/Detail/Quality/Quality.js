/**
 * @license
 * The MIT License (MIT)
 * Copyright 2015 Government of Canada
 *
 * @author
 * Ian Boyes
 *
 * @exports Quality
 */

'use strict';

import React from "react";
import { Panel } from 'react-bootstrap';
import { Icon, Button } from 'virtool/js/components/Base';

var Chart = require('./Chart');
var Bases = require('./Bases');
var Nucleotides = require('./Nucleotides');
var Sequences = require('./Sequences');



/**
 * A component that renders the three quality graphs associated with a sample given sample data.
 *
 * @class
 */
var SampleDetailQuality = React.createClass({

    propTypes: {
        _id: React.PropTypes.string.isRequired,
        quality: React.PropTypes.object.isRequired
    },

    getInitialState: function () {
        return {
            pending: false,
            download: null
        };
    },

    pdf: function () {
        this.setState({
            pending: true,
            download: null
        }, function () {
            dispatcher.db.samples.request('quality_pdf', {_id: this.props.data._id}).success(function (data) {
                this.setState({
                    pending: false,
                    download: data.file_id
                });
            }, this);
        });
    },

    render: function () {

        var buttonProps = {
            onClick: this.state.download ? null : this.pdf,
            bsStyle: this.state.download ? 'primary' : 'default',
            href: this.state.download ? 'download/' + this.state.download : null,
            download: this.state.download ? 'quality_' + this.props._id + '.pdf' : null
        };

        return (
            <Panel className="tab-panel">
                <div ref='container' className='printable-quality'>
                    <h5>
                        <strong>Quality Distribution at Read Positions</strong>
                        <Button bsSize='xsmall' {...buttonProps} pullRight>
                            <Icon name='file-pdf' pending={this.state.pending}/> PDF
                        </Button>
                    </h5>
                    <Chart
                        createChart={Bases}
                        data={this.props.quality.bases}
                    />

                    <h5><strong>Nucleotide Composition at Read Positions</strong></h5>
                    <Chart
                        createChart={Nucleotides}
                        data={this.props.quality.composition}
                    />

                    <h5><strong>Read-wise Quality Occurrence</strong></h5>
                    <Chart
                        createChart={Sequences}
                        data={this.props.quality.sequences}
                    />

                </div>
            </Panel>
        );
    }
});

module.exports = SampleDetailQuality;