import { capitalize, map } from "lodash-es";
import React from "react";
import { connect } from "react-redux";
import { updateSetting } from "../../administration/actions";
import { Panel, Radio } from "../../base";

export const ChannelButton = ({ channel, checked, onClick }) => (
    <Radio
        label={`${capitalize(channel)}${channel === "stable" ? " (recommended)" : ""}`}
        checked={checked}
        onClick={() => onClick(channel)}
    />
);

export const SoftwareChannels = ({ channel, onSetSoftwareChannel }) => {
    const radioComponents = map(["stable", "beta", "alpha"], label => (
        <ChannelButton key={label} channel={label} checked={label === channel} onClick={onSetSoftwareChannel} />
    ));

    return (
        <Panel>
            <Panel.Body>
                <label>Software Channel</label>
                {radioComponents}
            </Panel.Body>
        </Panel>
    );
};

export const mapStateToProps = state => ({
    channel: state.settings.data.software_channel
});

export const mapDispatchToProps = dispatch => ({
    onSetSoftwareChannel: value => {
        dispatch(updateSetting("software_channel", value));
    }
});

export default connect(
    mapStateToProps,
    mapDispatchToProps
)(SoftwareChannels);
