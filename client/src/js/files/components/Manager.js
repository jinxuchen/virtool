import { capitalize, forEach } from "lodash-es";
import React from "react";
import { connect } from "react-redux";
import { Icon, LoadingPlaceholder, NoneFound, ScrollList, UploadBar, ViewHeader, WarningAlert } from "../../base";
import { checkAdminOrPermission, createRandomString } from "../../utils/utils";
import { findFiles, upload } from "../actions";
import { filesSelector } from "../selectors";
import File from "./File";

class FileManager extends React.Component {
    componentDidMount() {
        this.props.onLoadNextPage(this.props.fileType, this.props.term, 1);
    }

    handleDrop = acceptedFiles => {
        if (this.props.canUpload) {
            this.props.onDrop(this.props.fileType, acceptedFiles);
        }
    };

    renderRow = index => <File key={index} index={index} />;

    render() {
        if (
            this.props.documents === null ||
            (this.props.storedFileType && this.props.fileType !== this.props.storedFileType)
        ) {
            return <LoadingPlaceholder />;
        }

        const titleType = this.props.fileType === "reads" ? "Read" : capitalize(this.props.fileType);

        let toolbar;

        if (this.props.canUpload) {
            toolbar = <UploadBar onDrop={this.handleDrop} />;
        } else {
            toolbar = (
                <WarningAlert level>
                    <Icon name="exclamation-circle" />
                    <span>
                        <strong>You do not have permission to upload files.</strong>
                        <span> Contact an administrator.</span>
                    </span>
                </WarningAlert>
            );
        }

        return (
            <div>
                <ViewHeader title={`${titleType} Files`} totalCount={this.props.total_count} />

                {toolbar}

                {this.props.documents.length ? null : <NoneFound noun="files" />}

                <ScrollList
                    documents={this.props.documents}
                    onLoadNextPage={page => this.props.onLoadNextPage(this.props.fileType, this.props.term, page)}
                    page={this.props.page}
                    pageCount={this.props.page_count}
                    renderRow={this.renderRow}
                />
            </div>
        );
    }
}

const mapStateToProps = state => {
    const { found_count, page, page_count, total_count } = state.files;

    return {
        documents: filesSelector(state),
        found_count,
        page,
        page_count,
        total_count,
        canUpload: checkAdminOrPermission(state, "upload_file"),
        storedFileType: state.files.fileType
    };
};

const mapDispatchToProps = dispatch => ({
    onDrop: (fileType, acceptedFiles) => {
        forEach(acceptedFiles, file => {
            const localId = createRandomString();
            dispatch(upload(localId, file, fileType));
        });
    },

    onLoadNextPage: (fileType, term, page = 1) => {
        dispatch(findFiles(fileType, term, page));
    }
});

export default connect(
    mapStateToProps,
    mapDispatchToProps
)(FileManager);
