import { get } from "lodash-es";
import React from "react";
import { Breadcrumb } from "react-bootstrap";
import { connect } from "react-redux";
import { LinkContainer } from "react-router-bootstrap";
import { Redirect, Route, Switch } from "react-router-dom";
import { Badge, LoadingPlaceholder, NotFound, RelativeTime, TabLink, Tabs, ViewHeader } from "../../base";
import { getIndex, getIndexHistory } from "../actions";
import IndexChanges from "./Changes";
import IndexGeneral from "./General";

export const IndexDetailBreadCrumb = ({ refDetail, version }) => (
    <Breadcrumb>
        <Breadcrumb.Item>
            <LinkContainer to="/refs/">
                <span>References</span>
            </LinkContainer>
        </Breadcrumb.Item>
        <Breadcrumb.Item>
            <LinkContainer to={`/refs/${refDetail.id}`}>
                <span>{refDetail.name}</span>
            </LinkContainer>
        </Breadcrumb.Item>
        <Breadcrumb.Item>
            <LinkContainer to={`/refs/${refDetail.id}/indexes`}>
                <span>Indexes</span>
            </LinkContainer>
        </Breadcrumb.Item>
        <Breadcrumb.Item active>Index {version}</Breadcrumb.Item>
    </Breadcrumb>
);

export class IndexDetail extends React.Component {
    componentDidMount() {
        this.props.onGetIndex(this.props.match.params.indexId);
        this.props.onGetChanges(this.props.match.params.indexId, 1);
    }

    render() {
        if (this.props.error) {
            return <NotFound />;
        }

        if (this.props.detail === null || this.props.refDetail === null) {
            return <LoadingPlaceholder />;
        }

        const indexId = this.props.detail.id;
        const { version, created_at, user } = this.props.detail;
        const refId = this.props.refDetail.id;

        return (
            <div>
                <IndexDetailBreadCrumb refDetail={this.props.refDetail} version={version} />

                <ViewHeader title={`Index ${version} - Indexes - Virtool`}>
                    <strong>Index {version}</strong>
                    <div className="text-muted" style={{ fontSize: "12px" }}>
                        Created <RelativeTime time={created_at} /> by {user.id}
                    </div>
                </ViewHeader>

                <Tabs>
                    <TabLink to={`/refs/${refId}/indexes/${indexId}/general`}>General</TabLink>
                    <TabLink to={`/refs/${refId}/indexes/${indexId}/changes`}>
                        Changes <Badge>{this.props.detail.change_count}</Badge>
                    </TabLink>
                </Tabs>

                <Switch>
                    <Redirect
                        from="/refs/:refId/indexes/:indexId"
                        to={`/refs/${refId}/indexes/${indexId}/general`}
                        exact
                    />
                    <Route path="/refs/:refId/indexes/:indexId/general" component={IndexGeneral} />
                    <Route path="/refs/:refId/indexes/:indexId/changes" component={IndexChanges} />
                </Switch>
            </div>
        );
    }
}

export const mapStateToProps = state => ({
    error: get(state, "errors.GET_INDEX_ERROR", null),
    detail: state.indexes.detail,
    refDetail: state.references.detail
});

export const mapDispatchToProps = dispatch => ({
    onGetIndex: indexId => {
        dispatch(getIndex(indexId));
    },

    onGetChanges: (indexId, page) => {
        dispatch(getIndexHistory(indexId, page));
    }
});

export default connect(
    mapStateToProps,
    mapDispatchToProps
)(IndexDetail);
