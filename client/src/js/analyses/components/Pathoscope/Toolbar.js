import React from "react";
import styled from "styled-components";
import { Dropdown, DropdownButton, FormControl, FormGroup, InputGroup, MenuItem } from "react-bootstrap";
import { connect } from "react-redux";
import { Button, Checkbox, Flex, FlexItem, Icon, Toolbar } from "../../../base";
import {
    collapseAnalysis,
    setAnalysisSortKey,
    setPathoscopeFilter,
    togglePathoscopeSortDescending,
    toggleShowPathoscopeReads
} from "../../actions";

export const PathoscopeDownloadDropdownTitle = () => (
    <span>
        <Icon name="file-download" /> Export
    </span>
);

const StyledPathoscopeToolbar = styled(Toolbar)`
    display: flex;
    margin-bottom: 10px !important;
`;

export const PathoscopeToolbar = ({
    analysisId,
    filterIsolates,
    filterOTUs,
    showReads,
    sortDescending,
    sortKey,
    onCollapse,
    onFilter,
    onSetSortKey,
    onToggleShowReads,
    onToggleSortDescending
}) => {
    return (
        <StyledPathoscopeToolbar>
            <FormGroup>
                <InputGroup>
                    <InputGroup.Button>
                        <Button title="Sort Direction" onClick={onToggleSortDescending} tip="Sort List">
                            <Icon name={sortDescending ? "sort-amount-down" : "sort-amount-up"} />
                        </Button>
                    </InputGroup.Button>
                    <FormControl componentClass="select" value={sortKey} onChange={e => onSetSortKey(e.target.value)}>
                        <option className="text-primary" value="coverage">
                            Coverage
                        </option>
                        <option className="text-success" value="pi">
                            Weight
                        </option>
                        <option className="text-danger" value="depth">
                            Depth
                        </option>
                    </FormControl>
                </InputGroup>
            </FormGroup>

            <Button
                icon="compress"
                title="Collapse"
                tip="Collapse"
                onClick={onCollapse}
                className="hidden-xs"
                disabled={false}
            />

            <Button
                icon="chart-pie"
                title="Weight Format"
                tip="Weight Format"
                active={!showReads}
                className="hidden-xs"
                onClick={onToggleShowReads}
            />

            <Dropdown
                id="pathoscope-filter-dropdown"
                onSelect={onFilter}
                className="split-dropdown"
                pullRight
                style={{ zIndex: 1 }}
            >
                <Button title="Filter" tip="Filter Results" onClick={onFilter} active={filterOTUs || filterIsolates}>
                    <Icon name="filter" />
                </Button>
                <Dropdown.Toggle />
                <Dropdown.Menu>
                    <MenuItem eventKey="OTUs">
                        <Flex>
                            <FlexItem>
                                <Checkbox checked={filterOTUs} />
                            </FlexItem>
                            <FlexItem pad={5}>OTUs</FlexItem>
                        </Flex>
                    </MenuItem>
                    <MenuItem eventKey="isolates">
                        <Flex>
                            <FlexItem>
                                <Checkbox checked={filterIsolates} />
                            </FlexItem>
                            <FlexItem pad={5}>Isolates</FlexItem>
                        </Flex>
                    </MenuItem>
                </Dropdown.Menu>
            </Dropdown>

            <DropdownButton
                id="download-dropdown"
                title={<PathoscopeDownloadDropdownTitle />}
                pullRight
                style={{ zIndex: 1 }}
            >
                <MenuItem href={`/download/analyses/${analysisId}.csv`}>
                    <Icon name="file-csv" /> CSV
                </MenuItem>
                <MenuItem href={`/download/analyses/${analysisId}.xlsx`}>
                    <Icon name="file-excel" /> Excel
                </MenuItem>
            </DropdownButton>
        </StyledPathoscopeToolbar>
    );
};

export const mapStateToProps = state => {
    const { filterIsolates, filterOTUs, showReads, sortDescending, sortKey } = state.analyses;
    return {
        analysisId: state.analyses.detail.id,
        filterIsolates,
        filterOTUs,
        showReads,
        sortDescending,
        sortKey
    };
};

export const mapDispatchToProps = dispatch => ({
    onCollapse: () => {
        dispatch(collapseAnalysis());
    },

    onFilter: key => {
        if (key !== "OTUs" && key !== "isolates") {
            key = "";
        }

        dispatch(setPathoscopeFilter(key));
    },

    onSetSortKey: key => {
        dispatch(setAnalysisSortKey(key));
    },

    onToggleSortDescending: () => {
        dispatch(togglePathoscopeSortDescending());
    },

    onToggleShowReads: () => {
        dispatch(toggleShowPathoscopeReads());
    }
});

export default connect(
    mapStateToProps,
    mapDispatchToProps
)(PathoscopeToolbar);
