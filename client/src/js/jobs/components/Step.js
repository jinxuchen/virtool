import Moment from "moment";
import React from "react";
import styled from "styled-components";
import { BoxGroupSection, Icon, Loader } from "../../base";
import { getStepDescription } from "../utils";

const StyledJobStepTimestamp = styled.div`
    align-items: center;
    display: flex;
    margin-top: 10px;

    i:not(:first-child) {
        padding-left: 10px;
    }

    & > span {
        padding-left: 5px;
    }
`;

const JobStepTimestamp = ({ timestamp }) => (
    <StyledJobStepTimestamp>
        <Icon name="clock" />
        <span>{Moment(timestamp).format("hh:mm:ss")}</span>
        <Icon name="calendar" />
        <span>{Moment(timestamp).format("YYYY-MM-DD")}</span>
    </StyledJobStepTimestamp>
);

const StyledJobStepDescription = styled.div`
    display: flex;
    flex-direction: column;
`;

export const JobStepDescription = ({ stage, state, task, timestamp }) => {
    const { description, title } = getStepDescription(stage, state, task);

    return (
        <StyledJobStepDescription>
            <strong>{title}</strong>
            <small className="text-muted">{description}</small>
            <JobStepTimestamp timestamp={timestamp} />
        </StyledJobStepDescription>
    );
};

export const JobStepIcon = ({ complete, state }) => {
    if (state === "waiting") {
        return <Icon name="pause" bsStyle="info" fixedWidth />;
    }

    if (complete) {
        return <Icon name="arrow-circle-down" bsStyle="primary" fixedWidth />;
    }

    if (state === "running") {
        return <Loader size="12px" color="#07689d" style={{ padding: "0 1.5px" }} />;
    }

    if (state === "complete") {
        return <Icon name="check" bsStyle="success" fixedWidth />;
    }

    if (state === "error") {
        return <Icon name="times" bsStyle="danger" fixedWidth />;
    }

    if (state === "cancelled") {
        return <Icon name="ban" bsStyle="danger" fixedWidth />;
    }
};

const JobStepIconContainer = styled.div`
    align-items: center;
    display: flex;
    height: 16px;
    margin-right: 4px;
    padding-top: 3px;
    width: 16px;
`;

const StyledJobStep = styled(BoxGroupSection)`
    align-items: flex-start;
    display: flex;
`;

const JobStep = ({ complete, step, task }) => (
    <StyledJobStep>
        <JobStepIconContainer>
            <JobStepIcon state={step.state} complete={complete} />
        </JobStepIconContainer>
        <JobStepDescription {...step} task={task} />
    </StyledJobStep>
);

export default JobStep;
